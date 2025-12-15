import discord
from discord.ext import commands
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='purge')
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10):
        """Elimina mensajes del canal"""
        if amount > 100:
            await ctx.send('❌ No puedes eliminar más de 100 mensajes a la vez')
            return
        
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f'✅ Se eliminaron {len(deleted)} mensajes', delete_after=5)

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason='Sin razón'):
        """Expulsa a un miembro del servidor"""
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title='⚠️ Miembro Expulsado',
                description=f'{member.mention} ha sido expulsado',
                color=0xFF0000
            )
            embed.add_field(name='Razón', value=reason)
            await ctx.send(embed=embed)
            logger.info(f'{member} fue expulsado por {ctx.author}: {reason}')
        except discord.Forbidden:
            await ctx.send(f'❌ No tengo permisos para expulsar a {member.mention}')
            logger.warning(f'Intento de expulsar a {member} sin permisos por {ctx.author}')
        except discord.HTTPException as e:
            await ctx.send(f'❌ Error de Discord al expulsar: {e}')
            logger.error(f'Error HTTP al expulsar a {member}: {e}')
        except Exception as e:
            await ctx.send(f'❌ Error inesperado al expulsar: {e}')
            logger.error(f'Error inesperado al expulsar a {member}: {e}')

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason='Sin razón'):
        """Banea a un miembro del servidor"""
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title='🚫 Miembro Baneado',
                description=f'{member.mention} ha sido baneado',
                color=0xFF0000
            )
            embed.add_field(name='Razón', value=reason)
            await ctx.send(embed=embed)
            logger.info(f'{member} fue baneado por {ctx.author}: {reason}')
        except discord.Forbidden:
            await ctx.send(f'❌ No tengo permisos para banear a {member.mention}')
            logger.warning(f'Intento de banear a {member} sin permisos por {ctx.author}')
        except discord.HTTPException as e:
            await ctx.send(f'❌ Error de Discord al banear: {e}')
            logger.error(f'Error HTTP al banear a {member}: {e}')
        except Exception as e:
            await ctx.send(f'❌ Error inesperado al banear: {e}')
            logger.error(f'Error inesperado al banear a {member}: {e}')

    @commands.command(name='mute')
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: int = 60, *, reason='Sin razón'):
        """Silencia a un miembro (duración en minutos)"""
        try:
            from datetime import timedelta
            await member.timeout(timedelta(minutes=duration), reason=reason)
            embed = discord.Embed(
                title='🔇 Miembro Silenciado',
                description=f'{member.mention} ha sido silenciado por {duration} minutos',
                color=0xFFFF00
            )
            embed.add_field(name='Razón', value=reason)
            await ctx.send(embed=embed)
            logger.info(f'{member} fue silenciado por {ctx.author} por {duration} min: {reason}')
        except discord.Forbidden:
            await ctx.send(f'❌ No tengo permisos para silenciar a {member.mention}')
            logger.warning(f'Intento de silenciar a {member} sin permisos por {ctx.author}')
        except discord.HTTPException as e:
            await ctx.send(f'❌ Error de Discord al silenciar: {e}')
            logger.error(f'Error HTTP al silenciar a {member}: {e}')
        except Exception as e:
            await ctx.send(f'❌ Error inesperado al silenciar: {e}')
            logger.error(f'Error inesperado al silenciar a {member}: {e}')

    @commands.command(name='unmute')
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Retira el silencio de un miembro"""
        try:
            await member.timeout(None)
            await ctx.send(f'✅ {member.mention} ha sido desilenciado')
            logger.info(f'{member} fue desilenciado por {ctx.author}')
        except discord.Forbidden:
            await ctx.send(f'❌ No tengo permisos para desilenciar a {member.mention}')
            logger.warning(f'Intento de desilenciar a {member} sin permisos por {ctx.author}')
        except discord.HTTPException as e:
            await ctx.send(f'❌ Error de Discord al desilenciar: {e}')
            logger.error(f'Error HTTP al desilenciar a {member}: {e}')
        except Exception as e:
            await ctx.send(f'❌ Error inesperado al desilenciar: {e}')
            logger.error(f'Error inesperado al desilenciar a {member}: {e}')

    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason='Sin razón'):
        """Advierte a un miembro"""
        embed = discord.Embed(
            title='⚠️ Advertencia',
            description=f'{member.mention} ha recibido una advertencia',
            color=0xFFFF00
        )
        embed.add_field(name='Razón', value=reason)
        embed.set_footer(text=f'Moderador: {ctx.author}')
        
        # Enviar en privado
        dm_status_message = ""
        try:
            await member.send(embed=embed)
            dm_status_message = f'✅ DM de advertencia enviado a {member.mention} con éxito.'
            logger.info(f'DM de advertencia enviado a {member}')
        except discord.Forbidden:
            dm_status_message = f'❌ No pude enviar un mensaje directo a {member.mention}. Es posible que tenga los DMs cerrados.'
            logger.warning(f'No se pudo enviar DM de advertencia a {member} (DMs cerrados)')
        except discord.HTTPException as e:
            dm_status_message = f'❌ Error de Discord al enviar DM de advertencia a {member.mention}: {e}'
            logger.error(f'Error HTTP al enviar DM de advertencia a {member}: {e}')
        except Exception as e:
            dm_status_message = f'❌ Error inesperado al enviar DM de advertencia a {member.mention}: {e}'
            logger.error(f'Error inesperado al enviar DM de advertencia a {member}: {e}')
        
        # Notificación pública en el canal
        await ctx.send(embed=embed)
        await ctx.send(dm_status_message) # Send the DM status message
        
        logger.info(f'{member} fue advertido por {ctx.author}: {reason}')

    @commands.command(name='userinfo')
    async def userinfo(self, ctx, member: discord.Member = None):
        """Muestra información de un usuario"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f'Información de {member.name}',
            color=member.color
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name='ID', value=member.id, inline=False)
        embed.add_field(name='Nombre', value=member.mention, inline=False)
        embed.add_field(name='Creada', value=member.created_at.strftime('%d/%m/%Y %H:%M'), inline=False)
        embed.add_field(name='Unida al servidor', value=member.joined_at.strftime('%d/%m/%Y %H:%M'), inline=False)
        embed.add_field(name='Roles', value=' '.join([r.mention for r in member.roles[1:]]) or 'Sin roles', inline=False)
        embed.add_field(name='Estado', value=f'{member.status}', inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='serverinfo')
    async def serverinfo(self, ctx):
        """Muestra información del servidor"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f'Información de {guild.name}',
            color=0xFF69B4
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name='ID', value=guild.id, inline=False)
        embed.add_field(name='Propietario', value=guild.owner.mention, inline=False)
        embed.add_field(name='Creado', value=guild.created_at.strftime('%d/%m/%Y %H:%M'), inline=False)
        embed.add_field(name='Miembros', value=guild.member_count, inline=False)
        embed.add_field(name='Canales', value=f'Texto: {len(guild.text_channels)} | Voz: {len(guild.voice_channels)}', inline=False)
        embed.add_field(name='Roles', value=len(guild.roles), inline=False)
        embed.add_field(name='Nivel de verificación', value=guild.verification_level, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        """Muestra el avatar de un usuario"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f'Avatar de {member.name}',
            color=member.color
        )
        embed.set_image(url=member.avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Muestra la latencia del bot"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f'🏓 Pong! Latencia: {latency}ms')

    @commands.command(name='help_custom')
    async def help_custom(self, ctx):
        """Muestra lista de comandos disponibles"""
        embed = discord.Embed(
            title='📚 Comandos Disponibles',
            description='Lista de todos los comandos del servidor',
            color=0xFF69B4
        )
        
        embed.add_field(
            name='👥 Moderación',
            value='`!purge [cantidad]` - Elimina mensajes\n'
                  '`!kick [usuario] [razón]` - Expulsa a un usuario\n'
                  '`!ban [usuario] [razón]` - Banea a un usuario\n'
                  '`!mute [usuario] [minutos] [razón]` - Silencia a un usuario\n'
                  '`!unmute [usuario]` - Desilencia a un usuario\n'
                  '`!warn [usuario] [razón]` - Advierte a un usuario',
            inline=False
        )
        
        embed.add_field(
            name='ℹ️ Información',
            value='`!userinfo [usuario]` - Información del usuario\n'
                  '`!serverinfo` - Información del servidor\n'
                  '`!avatar [usuario]` - Avatar del usuario\n'
                  '`!ping` - Latencia del bot',
            inline=False
        )
        
        embed.add_field(
            name='🎨 Roles',
            value='`!role_menu [tipo]` - Crea menú de roles\n'
                  '`!send_role_embeds` - Envía embeds de roles\n'
                  'Tipos: colors, pronouns, age, games',
            inline=False
        )
        
        embed.add_field(
            name='⚙️ Admin',
            value='`!setup` - Configura el servidor\n'
                  '`!help_custom` - Este mensaje',
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
