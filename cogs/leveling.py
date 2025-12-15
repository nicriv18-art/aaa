import discord
from discord.ext import commands, tasks
import json
import os
import logging
from datetime import datetime, timedelta
import random
from config.server_config import SERVER_CONFIG

logger = logging.getLogger(__name__)

# Archivo para guardar datos de niveles
LEVELS_FILE = 'data/user_levels.json'

# Sistema de 30 niveles con recompensas
class LevelingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldown = {}
        self.cooldown_time = 5
        self.load_levels()
        self.save_levels_loop.start()

    def load_levels(self):
        """Carga los datos de niveles desde archivo"""
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
            
            if os.path.exists(LEVELS_FILE):
                with open(LEVELS_FILE, 'r') as f:
                    data = json.load(f)
                    self.levels = data.get('levels', {})
                    self.xp_cooldown = data.get('xp_cooldown', {})
            else:
                self.levels = {}
                self.xp_cooldown = {}
                self.save_levels()
        except Exception as e:
            logger.error(f'Error cargando niveles: {e}')
            self.levels = {}

    def save_levels(self):
        """Guarda los datos de niveles"""
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
            
            with open(LEVELS_FILE, 'w') as f:
                json.dump({'levels': self.levels, 'xp_cooldown': self.xp_cooldown}, f, indent=2)
        except Exception as e:
            logger.error(f'Error guardando niveles: {e}')

    @tasks.loop(minutes=5)
    async def save_levels_loop(self):
        """Guarda niveles cada 5 minutos"""
        self.save_levels()
        logger.info('Niveles guardados automáticamente')

    def get_user_data(self, user_id: str):
        """Obtiene datos del usuario o crea uno nuevo"""
        if user_id not in self.levels:
            self.levels[user_id] = {
                'level': 1,
                'xp': 0,
                'total_xp': 0,
                'messages': 0,
                'last_xp_gain': datetime.now().isoformat()
            }
        return self.levels[user_id]

    def get_xp_for_level(self, level: int) -> int:
        """XP necesario para subir de nivel"""
        return 100 * level

    def get_level_from_xp(self, total_xp: int) -> tuple:
        """Retorna (level, current_xp) basado en XP total"""
        level = 1
        xp = total_xp
        
        while xp >= self.get_xp_for_level(level) and level < SERVER_CONFIG['MAX_LEVEL']:
            xp -= self.get_xp_for_level(level)
            level += 1
        
        return level, xp

    @commands.Cog.listener()
    async def on_message(self, message):
        """Otorga XP por mensajes"""
        if message.author.bot or not message.guild:
            return
        
        user_id = str(message.author.id)
        now = datetime.now()
        
        # Verificar cooldown
        if user_id in self.xp_cooldown:
            last_gain = datetime.fromisoformat(self.xp_cooldown[user_id])
            if (now - last_gain).total_seconds() < self.cooldown_time:
                return
        
        # Otorgar XP
        data = self.get_user_data(user_id)
        xp_gain = random.randint(10, 30)
        
        data['xp'] += xp_gain
        data['total_xp'] += xp_gain
        data['messages'] += 1
        self.xp_cooldown[user_id] = now.isoformat()
        
        # Verificar subida de nivel
        new_level, current_xp = self.get_level_from_xp(data['total_xp'])
        
        if new_level > data['level']:
            data['level'] = new_level
            data['xp'] = current_xp
            
            # Notificar al usuario
            embed = discord.Embed(
                title='🎉 ¡SUBIDA DE NIVEL!',
                description=f'{message.author.mention} ha alcanzado el **Nivel {new_level}**',
                color=SERVER_CONFIG['LEVEL_REWARDS'].get(new_level, {}).get('color', 0xFF69B4)
            )
            embed.set_thumbnail(url=message.author.avatar.url)
            
            try:
                level_up_channel_name = SERVER_CONFIG.get('level_up_channel', {}).get('name')
                if level_up_channel_name:
                    target_channel = discord.utils.get(message.guild.text_channels, name=level_up_channel_name)
                    if target_channel:
                        await target_channel.send(embed=embed)
                    else:
                        logger.warning(f"Canal de subida de nivel '{level_up_channel_name}' no encontrado. Enviando al canal actual.")
                        await message.channel.send(embed=embed)
                else:
                    await message.channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"No tengo permisos para enviar mensajes en el canal de subida de nivel o en el canal actual ({message.channel.name}).")
            except discord.HTTPException as e:
                logger.error(f"Error HTTP al enviar el mensaje de subida de nivel: {e}")
            except Exception as e:
                logger.error(f"Error inesperado al enviar el mensaje de subida de nivel: {e}")

    @commands.command(name='level')
    async def show_level(self, ctx, member: discord.Member = None):
        """Muestra el nivel de un usuario"""
        if member is None:
            member = ctx.author
        
        user_id = str(member.id)
        data = self.get_user_data(user_id)
        
        level = data['level']
        current_xp = data['xp']
        next_level_xp = self.get_xp_for_level(level)
        progress = (current_xp / next_level_xp * 100) if next_level_xp > 0 else 0
        
        embed = discord.Embed(
            title=f'📊 Estadísticas de {member.name}',
            color=SERVER_CONFIG['LEVEL_REWARDS'].get(level, {}).get('color', 0xFF69B4)
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name='📈 Nivel', value=f'**{level}**', inline=True)
        embed.add_field(name='⭐ XP Actual', value=f'**{current_xp}/{next_level_xp}**', inline=True)
        embed.add_field(name='💬 Mensajes', value=f'**{data["messages"]}**', inline=True)
        embed.add_field(
            name='📊 Progreso',
            value=f'```{progress:.1f}%```',
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx):
        """Muestra el top 10 de jugadores"""
        sorted_users = sorted(
            self.levels.items(),
            key=lambda x: x[1]['level'],
            reverse=True
        )[:10]
        
        embed = discord.Embed(
            title='🏆 Leaderboard del Servidor',
            color=0xFF69B4
        )
        
        for idx, (user_id, data) in enumerate(sorted_users, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(
                    name=f'{idx}. {user.name}',
                    value=f'Nivel **{data["level"]}** | Total XP: **{data["total_xp"]}**',
                    inline=False
                )
            except discord.NotFound:
                logger.warning(f'Usuario con ID {user_id} no encontrado para el leaderboard.')
            except discord.HTTPException as e:
                logger.error(f'Error HTTP al obtener usuario {user_id} para el leaderboard: {e}')
            except Exception as e:
                logger.error(f'Error inesperado al obtener usuario {user_id} para el leaderboard: {e}')
        
        await ctx.send(embed=embed)

    @commands.command(name='stats')
    async def server_stats(self, ctx):
        """Muestra estadísticas del servidor"""
        total_users = len(self.levels)
        total_xp = sum(data.get('total_xp', 0) for data in self.levels.values())
        total_messages = sum(data.get('messages', 0) for data in self.levels.values())
        
        avg_level = sum(data.get('level', 1) for data in self.levels.values()) / max(total_users, 1)
        
        highest = max(
            self.levels.items(),
            key=lambda x: x[1]['level'],
            default=(None, {'level': 0})
        )
        
        if highest[0]:
            try:
                top_user = await self.bot.fetch_user(int(highest[0]))
                top_user_name = top_user.name
            except discord.NotFound:
                top_user_name = 'Usuario Desconocido'
                logger.warning(f'Usuario con ID {highest[0]} no encontrado para estadísticas del servidor.')
            except discord.HTTPException as e:
                top_user_name = 'Error al obtener usuario'
                logger.error(f'Error HTTP al obtener usuario {highest[0]} para estadísticas del servidor: {e}')
            except Exception as e:
                top_user_name = 'Error inesperado'
                logger.error(f'Error inesperado al obtener usuario {highest[0]} para estadísticas del servidor: {e}')
        else:
            top_user_name = 'Ninguno'
        
        embed = discord.Embed(
            title='📈 Estadísticas del Servidor',
            color=0xFF69B4
        )
        embed.add_field(name='👥 Usuarios Activos', value=f'**{total_users}**', inline=True)
        embed.add_field(name='⭐ XP Total', value=f'**{total_xp}**', inline=True)
        embed.add_field(name='💬 Mensajes Totales', value=f'**{total_messages}**', inline=True)
        embed.add_field(name='📊 Nivel Promedio', value=f'**{avg_level:.1f}**', inline=True)
        embed.add_field(name='🏆 Usuario Más Avanzado', value=f'**{top_user_name}** - Nivel {highest[1]["level"]}', inline=True)
        embed.set_footer(text='Estadísticas en tiempo real del servidor')
        
        await ctx.send(embed=embed)

    @commands.command(name='resetlevel')
    @commands.has_permissions(administrator=True)
    async def reset_level(self, ctx, member: discord.Member):
        """Resetea el nivel de un usuario (solo admin)"""
        user_id = str(member.id)
        
        if user_id in self.levels:
            self.levels[user_id] = {
                'level': 1,
                'xp': 0,
                'total_xp': 0,
                'messages': 0,
                'last_xp_gain': datetime.now().isoformat()
            }
            self.save_levels()
        
        embed = discord.Embed(
            title='✅ Nivel Resetado',
            description=f'El nivel de {member.mention} ha sido reseteado a Nivel 1',
            color=0xFF69B4
        )
        await ctx.send(embed=embed)
        logger.info(f'{member} ({member.id}) tuvo su nivel reseteado por {ctx.author}')

    def cog_unload(self):
        """Se ejecuta cuando el cog se descarga"""
        self.save_levels_loop.cancel()
        self.save_levels()

async def setup(bot):
    await bot.add_cog(LevelingSystem(bot))
