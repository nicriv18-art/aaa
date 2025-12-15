import discord
from discord.ext import commands, tasks
import json
import os
import logging
from datetime import datetime
import aiohttp

from config.server_config import FILE_PATHS

logger = logging.getLogger(__name__)

# Archivo para guardar configuración de streamers


class TwitchNotifications(commands.Cog):
    """Sistema de notificaciones de directos en Twitch"""
    
    def __init__(self, bot):
        self.bot = bot
        self.twitch_api_key = os.getenv('TWITCH_API_KEY', '')  # Será configurado después
        self.twitch_client_id = os.getenv('TWITCH_CLIENT_ID', '')  # Será configurado después
        self.load_streamers()
        self.check_streams.start()

    def load_streamers(self):
        """Carga la lista de streamers a monitorear"""
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
            
            if os.path.exists(FILE_PATHS['twitch_streamers']):
                with open(FILE_PATHS['twitch_streamers'], 'r') as f:
                    self.streamers = json.load(f)
            else:
                self.streamers = {}
                self.save_streamers()
        except Exception as e:
            logger.error(f'Error cargando streamers de Twitch: {e}')
            self.streamers = {}

    def save_streamers(self):
        """Guarda la lista de streamers"""
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
            
            with open(FILE_PATHS['twitch_streamers'], 'w') as f:
                json.dump(self.streamers, f, indent=4)
        except Exception as e:
            logger.error(f'Error guardando streamers de Twitch: {e}')

    @tasks.loop(minutes=5)
    async def check_streams(self):
        """Verifica periódicamente si los streamers están en directo"""
        if not self.twitch_api_key or not self.twitch_client_id:
            # API no configurada aún
            return
        
        for guild_id, config in self.streamers.items():
            try:
                guild = self.bot.get_guild(int(guild_id))
                if not guild:
                    continue
                
                for streamer in config.get('streamers', []):
                    await self.check_streamer_status(guild, streamer)
            except Exception as e:
                logger.error(f'Error verificando streams: {e}')

    @check_streams.before_loop
    async def before_check_streams(self):
        await self.bot.wait_until_ready()

    async def check_streamer_status(self, guild, streamer_info):
        """Verifica si un streamer está en directo"""
        try:
            if not self.twitch_api_key or not self.twitch_client_id:
                return
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Client-ID': self.twitch_client_id,
                    'Authorization': f'Bearer {self.twitch_api_key}'
                }
                
                # Verificar si el streamer está en directo
                url = f"https://api.twitch.tv/helix/streams?user_login={streamer_info['username']}"
                
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if data['data']:
                            # El streamer está en directo
                            stream_info = data['data'][0]
                            
                            # Verificar si ya se notificó
                            if not streamer_info.get('is_live', False):
                                # Enviar notificación
                                await self.send_stream_notification(guild, streamer_info, stream_info)
                                streamer_info['is_live'] = True
                                streamer_info['last_notified'] = datetime.now().isoformat()
                        else:
                            # El streamer no está en directo
                            streamer_info['is_live'] = False
                        
                        self.save_streamers()
        except aiohttp.ClientError as e:
            logger.error(f'Error de cliente HTTP al verificar status del streamer: {e}')
        except json.JSONDecodeError as e:
            logger.error(f'Error de decodificación JSON al verificar status del streamer: {e}')
        except KeyError as e:
            logger.error(f'Error de clave (estructura de datos inesperada) al verificar status del streamer: {e}')
        except Exception as e:
            logger.error(f'Error inesperado al verificar status del streamer: {e}')

    async def send_stream_notification(self, guild, streamer_info, stream_info):
        """Envía una notificación de directo a Discord"""
        try:
            guild_config = self.streamers.get(str(guild.id), {})
            channel_id = guild_config.get('notification_channel')
            
            if not channel_id:
                return
            
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return
            
            # Crear embed con información del stream
            embed = discord.Embed(
                title=f'🔴 ¡{streamer_info["name"]} está en directo!',
                description=stream_info['title'],
                url=f'https://twitch.tv/{streamer_info["username"]}',
                color=0x9146FF  # Color de Twitch
            )
            
            embed.add_field(
                name='📺 Juego',
                value=stream_info.get('game_name', 'Sin especificar'),
                inline=True
            )
            embed.add_field(
                name='👥 Espectadores',
                value=f"{stream_info['viewer_count']} personas viendo",
                inline=True
            )
            embed.add_field(
                name='⏱️ En directo desde',
                value=stream_info['started_at'],
                inline=False
            )
            
            # Obtener imagen del stream
            if stream_info.get('thumbnail_url'):
                embed.set_image(url=stream_info['thumbnail_url'])
            
            embed.set_footer(text='Notificación de Twitch')
            
            # Obtener rol de mención si existe
            mention_role_id = guild_config.get('mention_role')
            mention = ''
            
            if mention_role_id:
                role = guild.get_role(int(mention_role_id))
                if role:
                    mention = role.mention
            
            # Enviar mensaje
            message = f"{mention} {streamer_info.get('custom_message', '')}"
            await channel.send(message if message.strip() else '', embed=embed)
            
            logger.info(f'Notificación enviada: {streamer_info["username"]} en directo')
        except discord.Forbidden:
            logger.warning(f'No tengo permisos para enviar mensajes en el canal {channel_id} del gremio {guild.name}')
        except discord.HTTPException as e:
            logger.error(f'Error HTTP de Discord al enviar notificación de stream: {e}')
        except Exception as e:
            logger.error(f'Error inesperado enviando notificación de stream: {e}')

    @commands.group(name='twitch', invoke_without_command=True)
    async def twitch(self, ctx):
        """Comandos de Twitch"""
        embed = discord.Embed(
            title='🎮 Comandos de Twitch',
            description='Gestiona notificaciones de directos en Twitch',
            color=0x9146FF
        )
        embed.add_field(
            name='Subcomandos disponibles:',
            value='`!twitch add [usuario]` - Añadir streamer a monitorear\n'
                  '`!twitch remove [usuario]` - Remover streamer\n'
                  '`!twitch list` - Ver lista de streamers\n'
                  '`!twitch channel [#canal]` - Configurar canal de notificaciones\n'
                  '`!twitch role [@rol]` - Configurar rol a mencionar (opcional)',
            inline=False
        )
        embed.set_footer(text='Nota: Requiere TWITCH_API_KEY y TWITCH_CLIENT_ID configurados en .env')
        
        await ctx.send(embed=embed)

    @twitch.command(name='add')
    @commands.has_permissions(administrator=True)
    async def add_streamer(self, ctx, username: str, name: str = None, *, custom_message: str = None):
        """Añade un streamer a monitorear
        Uso: !twitch add username [Nombre Visible] [Mensaje Personalizado]
        """
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.streamers:
            self.streamers[guild_id] = {
                'streamers': [],
                'notification_channel': None,
                'mention_role': None
            }
        
        # Verificar si ya existe
        for streamer in self.streamers[guild_id]['streamers']:
            if streamer['username'].lower() == username.lower():
                await ctx.send('❌ Este streamer ya está en la lista')
                return
        
        # Añadir streamer
        streamer_info = {
            'username': username.lower(),
            'name': name or username,
            'is_live': False,
            'last_notified': None,
            'custom_message': custom_message or f'¡{name or username} está en directo! 🔴'
        }
        
        self.streamers[guild_id]['streamers'].append(streamer_info)
        self.save_streamers()
        
        embed = discord.Embed(
            title='✅ Streamer Añadido',
            description=f'Ahora se monitorea a **{name or username}**',
            color=0x9146FF
        )
        embed.add_field(
            name='⚙️ Próximos pasos:',
            value='1. Configura el canal: `!twitch channel #canal`\n'
                  '2. (Opcional) Configura rol: `!twitch role @rol`',
            inline=False
        )
        await ctx.send(embed=embed)

    @twitch.command(name='remove')
    @commands.has_permissions(administrator=True)
    async def remove_streamer(self, ctx, username: str):
        """Remover un streamer de monitoreo"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.streamers:
            await ctx.send('❌ No hay streamers configurados')
            return
        
        original_count = len(self.streamers[guild_id]['streamers'])
        self.streamers[guild_id]['streamers'] = [
            s for s in self.streamers[guild_id]['streamers']
            if s['username'].lower() != username.lower()
        ]
        
        if len(self.streamers[guild_id]['streamers']) < original_count:
            self.save_streamers()
            await ctx.send(f'✅ **{username}** ha sido removido de la lista')
        else:
            await ctx.send('❌ Streamer no encontrado')

    @twitch.command(name='list')
    async def list_streamers(self, ctx):
        """Ver lista de streamers siendo monitoreados"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.streamers or not self.streamers[guild_id]['streamers']:
            await ctx.send('❌ No hay streamers configurados en este servidor')
            return
        
        embed = discord.Embed(
            title='📺 Streamers Siendo Monitoreados',
            color=0x9146FF
        )
        
        for streamer in self.streamers[guild_id]['streamers']:
            status = '🔴 EN DIRECTO' if streamer['is_live'] else '⚪ Offline'
            embed.add_field(
                name=f"{streamer['name']}",
                value=f"Usuario: `{streamer['username']}`\nEstado: {status}",
                inline=False
            )
        
        embed.set_footer(text=f'Total: {len(self.streamers[guild_id]["streamers"])} streamers')
        
        await ctx.send(embed=embed)

    @twitch.command(name='channel')
    @commands.has_permissions(administrator=True)
    async def set_notification_channel(self, ctx, channel: discord.TextChannel):
        """Configura el canal donde se enviarán notificaciones"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.streamers:
            self.streamers[guild_id] = {
                'streamers': [],
                'notification_channel': None,
                'mention_role': None
            }
        
        self.streamers[guild_id]['notification_channel'] = str(channel.id)
        self.save_streamers()
        
        await ctx.send(f'✅ Canal de notificaciones configurado: {channel.mention}')

    @twitch.command(name='role')
    @commands.has_permissions(administrator=True)
    async def set_mention_role(self, ctx, role: discord.Role):
        """Configura el rol a mencionar en notificaciones (opcional)"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.streamers:
            self.streamers[guild_id] = {
                'streamers': [],
                'notification_channel': None,
                'mention_role': None
            }
        
        self.streamers[guild_id]['mention_role'] = str(role.id)
        self.save_streamers()
        
        await ctx.send(f'✅ Rol configurado: {role.mention}')

    @twitch.command(name='status')
    async def twitch_status(self, ctx):
        """Ver estado de configuración de Twitch"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.streamers:
            config = {
                'streamers': [],
                'notification_channel': None,
                'mention_role': None
            }
        else:
            config = self.streamers[guild_id]
        
        embed = discord.Embed(
            title='🎮 Estado de Configuración Twitch',
            color=0x9146FF
        )
        
        # API Status
        api_status = '✅ Configurado' if (self.twitch_api_key and self.twitch_client_id) else '❌ No configurado'
        embed.add_field(name='API de Twitch', value=api_status, inline=False)
        
        # Canal de notificaciones
        if config['notification_channel']:
            channel = ctx.guild.get_channel(int(config['notification_channel']))
            channel_name = channel.mention if channel else 'Canal eliminado'
        else:
            channel_name = '❌ No configurado'
        embed.add_field(name='Canal de Notificaciones', value=channel_name, inline=False)
        
        # Rol de mención
        if config['mention_role']:
            role = ctx.guild.get_role(int(config['mention_role']))
            role_name = role.mention if role else 'Rol eliminado'
        else:
            role_name = '❌ No configurado (opcional)'
        embed.add_field(name='Rol a Mencionar', value=role_name, inline=False)
        
        # Streamers
        embed.add_field(
            name='Streamers Monitoreados',
            value=f'**{len(config["streamers"])}** streamers',
            inline=False
        )
        
        embed.set_footer(text='Usa !twitch para ver comandos disponibles')
        
        await ctx.send(embed=embed)

async def setup(bot):
    # Solo cargar si el cog está habilitado
    await bot.add_cog(TwitchNotifications(bot))
    logger.info('Cog de Twitch Notifications cargado (preconfigurado)')
