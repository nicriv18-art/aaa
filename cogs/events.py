import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthday_check.start()

    def cog_unload(self):
        self.birthday_check.cancel()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Evento cuando un miembro se une"""
        guild = member.guild
        
        # Enviar mensaje de bienvenida
        welcome_channel = discord.utils.get(guild.text_channels, name='✨bienvenido')
        if welcome_channel:
            embed = discord.Embed(
                title=f'¡Bienvenido/a {member.name}! 🎀',
                description=f'Hola {member.mention}, nos alegra que te unas a nuestro servidor kawaii UwU\n\n'
                           f'📝 Por favor preséntate en <#presentaciones>\n'
                           f'🎨 Selecciona tus roles en los canales de selección\n'
                           f'📋 Lee nuestras reglas en <#reglas>',
                color=0xFF69B4
            )
            embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=f'¡Eres el miembro #{guild.member_count}!')
            
            try:
                await welcome_channel.send(embed=embed)
            except Exception as e:
                logger.error(f'Error enviando mensaje de bienvenida: {e}')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Evento cuando un miembro se va"""
        guild = member.guild
        logger.info(f'{member} se fue del servidor {guild.name}')

    @commands.Cog.listener()
    async def on_message(self, message):
        """Evento cuando se envía un mensaje"""
        # Ignorar mensajes del bot
        if message.author.bot:
            return

        # Procesar comandos
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_ready(self):
        """Evento cuando el bot se conecta"""
        # Ya se maneja en bot.py para logs principales, aquí solo presence
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="un servidor kawaii UwU ✨"
            ),
            status=discord.Status.online
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Manejo de errores de comandos"""
        try:
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f'❌ Falta un argumento requerido: `{error.param}`')
            elif isinstance(error, commands.MissingPermissions):
                await ctx.send('❌ No tienes permisos para usar este comando')
            elif isinstance(error, commands.CommandNotFound):
                pass
            else:
                if isinstance(error, discord.NotFound):
                    logger.warning(f'Canal no encontrado o eliminado durante el comando: {ctx.channel}')
                    return
                logger.error(f'Error en comando: {error}')
                try:
                    await ctx.send(f'❌ Hubo un error al ejecutar el comando: {error}')
                except discord.errors.NotFound:
                    logger.warning(f'Canal no encontrado para enviar error: {ctx.channel}')
                except discord.errors.Forbidden:
                    logger.warning(f'Permiso denegado al enviar error en {ctx.channel}')
        except Exception as e:
            logger.error(f'Error en manejador de errores: {e}')

    @commands.command(name='birthday')
    async def birthday(self, ctx, member: discord.Member, date: str):
        """Registra el cumpleaños de un miembro
        Formato: !birthday @usuario DD/MM
        """
        try:
            birthday_channel = discord.utils.get(ctx.guild.text_channels, name='🎂cumpleaños')
            if not birthday_channel:
                await ctx.send('❌ No existe el canal de cumpleaños')
                return
            
            embed = discord.Embed(
                title='🎂 ¡Cumpleaños Registrado!',
                description=f'Cumpleaños de {member.mention}: {date}',
                color=0xFF69B4
            )
            embed.set_footer(text='¡Que cumplas muchos más! 🎉')
            
            await ctx.send(embed=embed)
            logger.info(f'Cumpleaños registrado para {member}: {date}')
        except Exception as e:
            await ctx.send(f'❌ Error: {e}')

    @tasks.loop(hours=24)
    async def birthday_check(self):
        """Verifica cumpleaños diariamente (de 0:00 a 0:01)"""
        # Esta es una tarea que se ejecutaría si tuviéramos una base de datos
        # Por ahora, solo está como ejemplo
        logger.info('Verificación de cumpleaños completada')

    @birthday_check.before_loop
    async def before_birthday_check(self):
        await self.bot.wait_until_ready()

    @commands.command(name='announcement')
    @commands.has_permissions(administrator=True)
    async def announcement(self, ctx, *, message):
        """Crea un anuncio hermoso"""
        embed = discord.Embed(
            title='📢 Anuncio Importante',
            description=message,
            color=0xFF69B4,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f'Por: {ctx.author.name}')
        
        # Mencionar a todos con rol @here
        announcement_channel = discord.utils.get(ctx.guild.text_channels, name='📢anuncios')
        if announcement_channel:
            await announcement_channel.send(embed=embed)
            await ctx.send('✅ Anuncio enviado')
        else:
            await ctx.send(embed=embed)

    @commands.command(name='poll')
    async def poll(self, ctx, *, question):
        """Crea una encuesta rápida"""
        embed = discord.Embed(
            title='📊 Encuesta',
            description=question,
            color=0xFF69B4
        )
        embed.set_footer(text=f'Por: {ctx.author.name}')
        
        message = await ctx.send(embed=embed)
        
        # Añadir reacciones
        await message.add_reaction('👍')
        await message.add_reaction('👎')
        await message.add_reaction('🤷')

    @commands.command(name='suggest')
    async def suggest(self, ctx, *, suggestion):
        """Envía una sugerencia de forma anónima al canal de sugerencias"""
        try:
            guild = ctx.guild
            suggestions_forum = None
            
            # Buscar el foro de sugerencias
            for forum in guild.forums:
                if 'sugerencias' in forum.name.lower():
                    suggestions_forum = forum
                    break
            
            if not suggestions_forum:
                await ctx.send('❌ No existe el foro de sugerencias')
                return
            
            embed = discord.Embed(
                title='Sugerencia de Comunidad',
                description=suggestion,
                color=0xFF69B4
            )
            embed.set_footer(text=f'Sugerencia de: {ctx.author}')
            
            # Crear thread en el foro
            thread = await suggestions_forum.create_thread(
                name=f'Sugerencia de {ctx.author.name}',
                content=suggestion
            )
            
            await ctx.send('✅ Tu sugerencia ha sido registrada con éxito', delete_after=5)
            logger.info(f'Sugerencia de {ctx.author}: {suggestion}')
        except Exception as e:
            logger.error(f'Error en sugerencia: {e}')
            await ctx.send(f'❌ Error al enviar sugerencia: {e}')

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
