import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio

logger = logging.getLogger(__name__)

class ServerSetupCustom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='setup_custom')
    @commands.has_permissions(administrator=True)
    async def setup_server_custom(self, ctx):
        """Configura el servidor con estructura personalizada"""
        guild = ctx.guild
        
        # Verificación de permisos del BOT
        if not guild.me.guild_permissions.manage_roles or not guild.me.guild_permissions.manage_channels:
            await ctx.send("❌ **ERROR DE PERMISOS:** No tengo permiso para gestionar roles o canales.\n"
                           "Necesito permisos de **Administrador** o **Gestionar Roles** y **Gestionar Canales**.")
            return

        try:
            embed = discord.Embed(
                title="🔧 CONFIGURACIÓN PERSONALIZADA DEL SERVIDOR",
                description="Iniciando proceso de configuración en segundo plano...",
                color=0xFF69B4
            )
            await ctx.send(embed=embed)
        except:
            pass

        # Ejecutar setup en segundo plano sin esperar
        asyncio.create_task(self._run_setup(guild))

    async def _run_setup(self, guild):
        """Ejecuta el setup en segundo plano"""
        try:
            logger.info(f'Iniciando setup personalizado en {guild.name}')
            # Crear roles
            created_roles = await self.create_roles(guild)
            logger.info(f'✅ {len(created_roles)} roles creados')
            
            # Crear categorías y canales
            await self.create_categories_and_channels(guild, created_roles)
            logger.info(f'✅ Categorías y canales creados')
            
            # Mensaje de finalización en el primer canal disponible
            for channel in guild.text_channels:
                try:
                    embed = discord.Embed(
                        title="✅ ¡SERVIDOR CONFIGURADO!",
                        description="Estructura personalizada creada correctamente.",
                        color=0x00FF00
                    )
                    await channel.send(embed=embed)
                    break
                except:
                    continue
            
        except Exception as e:
            logger.error(f'Error en setup personalizado: {e}')
            for channel in guild.text_channels:
                try:
                    await channel.send(f'❌ Error en configuración: {e}')
                    break
                except:
                    continue

    async def create_roles(self, guild):
        """Crea todos los roles con la estructura personalizada"""
        roles_to_create = [
            {"name": "Katsumi 3.0", "permissions": discord.Permissions.all(), "color": discord.Color.dark_red()},
            {"name": "Owner luministic", "permissions": discord.Permissions.all(), "color": discord.Color.gold()},
            {"name": "Co-Owner darkness", "permissions": discord.Permissions.all(), "color": discord.Color.dark_purple()},
            {"name": "Admin", "permissions": discord.Permissions(kick_members=True, ban_members=True, manage_channels=True, manage_roles=True, manage_messages=True, mute_members=True, deafen_members=True, move_members=True), "color": discord.Color.red()},
            {"name": "Mod pesesito", "permissions": discord.Permissions(kick_members=True, manage_messages=True, mute_members=True, deafen_members=True, move_members=True), "color": discord.Color.orange()},
            {"name": "Mod ervinardo", "permissions": discord.Permissions(kick_members=True, manage_messages=True, mute_members=True, deafen_members=True, move_members=True), "color": discord.Color.orange()},
            {"name": "Confianza", "permissions": discord.Permissions(read_messages=True, read_message_history=True, send_messages=True, add_reactions=True, attach_files=True, connect=True, speak=True), "color": discord.Color.blue()},
            {"name": "♡Los peepsitos", "permissions": discord.Permissions(read_messages=True, read_message_history=True, send_messages=True, add_reactions=True, attach_files=True, connect=True, speak=True, use_voice_activation=True), "color": discord.Color.purple()},
            
            # Roles de Bot
            {"name": "Bot", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "carl-bot", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Nekotina", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Ticket King", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "MatchBox", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Pez", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            
            # Roles de Color
            {"name": "Rosa", "permissions": discord.Permissions.none(), "color": discord.Color.pink()},
            {"name": "Rojo", "permissions": discord.Permissions.none(), "color": discord.Color.red()},
            {"name": "Morado", "permissions": discord.Permissions.none(), "color": discord.Color.purple()},
            {"name": "Naranja", "permissions": discord.Permissions.none(), "color": discord.Color.orange()},
            {"name": "Amarillo", "permissions": discord.Permissions.none(), "color": discord.Color.gold()},
            {"name": "Verde", "permissions": discord.Permissions.none(), "color": discord.Color.green()},
            {"name": "Azul", "permissions": discord.Permissions.none(), "color": discord.Color.blue()},
            {"name": "Blanco", "permissions": discord.Permissions.none(), "color": discord.Color.lighter_grey()},
            {"name": "Negro", "permissions": discord.Permissions.none(), "color": discord.Color.dark_grey()},
            {"name": "Sapphire", "permissions": discord.Permissions.none(), "color": discord.Color.blue()},
            
            # Roles de Edad
            {"name": "13-15", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "16-17", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "18+", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            
            # Roles de Pronombres
            {"name": "he/him", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "she/her", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "they/them", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "any/pronouns", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            
            # Roles de Juegos/Intereses
            {"name": "Overwatch 2", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Valorant", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "GTA V", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Resident Evil", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Dead by Daylight", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "League of Legends", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Osu!", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Roblox", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Animal Crossing", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Stardew Valley", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "The Sims", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Hollow Knight", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Pokémon", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Needy Streamer Overload", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Phasmophobia", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Fall Guys", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Notificaciones", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Gamers", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "War Thunder", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Elden Ring", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Genshin Impact", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Marvel Rivals", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Wuthering Waves", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "ARC Raiders", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Minecraft", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Stuck in aquarium", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "ENGLISH BOY GB", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
            {"name": "Cumpleaños 🎂", "permissions": discord.Permissions.none(), "color": discord.Color.light_grey()},
        ]
        
        created_roles = {}
        for role_data in roles_to_create:
            try:
                # Verificar si existe
                existing = discord.utils.get(guild.roles, name=role_data['name'])
                if existing:
                    created_roles[role_data['name']] = existing
                    logger.info(f'⏭️ Rol ya existe: {role_data["name"]}')
                    continue
                
                role = await guild.create_role(
                    name=role_data['name'],
                    permissions=role_data.get('permissions', discord.Permissions.none()),
                    color=role_data.get('color', discord.Color.default()),
                    reason='Setup personalizado'
                )
                created_roles[role_data['name']] = role
                logger.info(f'✅ Rol creado: {role_data["name"]}')
                await asyncio.sleep(1.5)  # Mayor delay para evitar rate limiting
            except Exception as e:
                logger.error(f'❌ Error creando {role_data["name"]}: {e}')
        
        return created_roles

    async def create_categories_and_channels(self, guild, created_roles):
        """Crea categorías y canales con permisos específicos"""
        everyone_role = guild.default_role
        
        # Definir permisos reutilizables
        staff_overwrites = {
            everyone_role: discord.PermissionOverwrite(view_channel=False),
        }
        
        everyone_overwrites = {
            everyone_role: discord.PermissionOverwrite(send_messages=True, view_channel=True),
        }
        
        peepsitos_overwrites = {
            everyone_role: discord.PermissionOverwrite(send_messages=True, view_channel=True),
        }
        
        # Estructura de categorías y canales
        categories_and_channels = {
            "~- jeloudah 👑!": {
                "overwrites": {
                    everyone_role: discord.PermissionOverwrite(send_messages=False, view_channel=True),
                },
                "channels": [
                    {"name": "📜・normitas-del-lugar", "type": "text"},
                    {"name": "✨・roles-y-cositas", "type": "text"},
                ]
            },
            "📢 anuncios": {
                "overwrites": {
                    everyone_role: discord.PermissionOverwrite(send_messages=False, view_channel=True),
                },
                "channels": [
                    {"name": "📢・anuncios", "type": "text"},
                    {"name": "🎆・eventos-epicos", "type": "text"},
                ]
            },
            "💬 texto-general": {
                "overwrites": everyone_overwrites,
                "channels": [
                    {"name": "💬・charlita-general", "type": "text"},
                    {"name": "🔥・venting-zone", "type": "text"},
                    {"name": "🤖・comandos-bot", "type": "text"},
                    {"name": "🌲・navidad-2025", "type": "text"},
                    {"name": "🎂 cumplitos", "type": "text"},
                ]
            },
            "🎮 entretenimiento": {
                "overwrites": everyone_overwrites,
                "channels": [
                    {"name": "😼・memardos-premium", "type": "text"},
                    {"name": "🎨・cositas-creativas", "type": "text"},
                    {"name": "🎬・clips", "type": "text"},
                    {"name": "🦊・animalitos", "type": "text"},
                    {"name": "📸・fotos", "type": "text"},
                    {"name": "🧑‍🤝‍🧑 face-reveal", "type": "text"},
                    {"name": "👤 Yo", "type": "text"},
                ]
            },
            "🎮 videojuegos-y-consolas": {
                "overwrites": everyone_overwrites,
                "channels": [
                    {"name": "🎮・gaming-chat", "type": "text"},
                ]
            },
            "🎧 voz": {
                "overwrites": {
                    everyone_role: discord.PermissionOverwrite(connect=True, speak=True, view_channel=True),
                },
                "channels": [
                    {"name": "🗣️・charla-en-voz", "type": "voice"},
                    {"name": "🎶・musiquita-uwu", "type": "voice"},
                    {"name": "🎮・gaming-call", "type": "voice"},
                    {"name": "🎮・gaming-call-2", "type": "voice"},
                    {"name": "😴・afk-room", "type": "voice"},
                    {"name": "🗣️ a comer tetotas en vinagre", "type": "voice"},
                    {"name": "🗣️ Shadow realm", "type": "voice"},
                ]
            },
            "🎫 zona-de-tickets": {
                "overwrites": everyone_overwrites,
                "channels": [
                    {"name": "🎫・crear-ticket", "type": "text"},
                    {"name": "📂・tickets-activos", "type": "text"},
                    {"name": "✅・tickets-cerrados", "type": "text"},
                ]
            },
            "🛠️ control-del-staff": {
                "overwrites": {
                    everyone_role: discord.PermissionOverwrite(view_channel=False),
                },
                "channels": [
                    {"name": "🛠️・staff-hub", "type": "text"},
                    {"name": "🗃️・logs-secretos", "type": "text"},
                    {"name": "📝・registro-del-reino", "type": "text"},
                ]
            },
            "❗ Staff": {
                "overwrites": {
                    everyone_role: discord.PermissionOverwrite(view_channel=False),
                },
                "channels": [
                    {"name": "❓・dudas", "type": "text"},
                ]
            },
        }
        
        # Crear categorías y canales
        for category_name, category_data in categories_and_channels.items():
            try:
                # Verificar si la categoría ya existe
                existing_cat = discord.utils.get(guild.categories, name=category_name)
                if existing_cat:
                    category = existing_cat
                    logger.info(f'⏭️ Categoría ya existe: {category_name}')
                else:
                    category = await guild.create_category(
                        name=category_name,
                        overwrites=category_data.get('overwrites', {}),
                        reason='Setup personalizado'
                    )
                    logger.info(f'✅ Categoría creada: {category_name}')
                
                # Crear canales en la categoría
                for channel_data in category_data.get('channels', []):
                    try:
                        existing_ch = discord.utils.get(guild.channels, name=channel_data['name'])
                        if existing_ch:
                            logger.info(f'⏭️ Canal ya existe: {channel_data["name"]}')
                            continue
                        
                        if channel_data['type'] == 'text':
                            await guild.create_text_channel(
                                name=channel_data['name'],
                                category=category,
                                reason='Setup personalizado'
                            )
                        elif channel_data['type'] == 'voice':
                            await guild.create_voice_channel(
                                name=channel_data['name'],
                                category=category,
                                reason='Setup personalizado'
                            )
                        
                        logger.info(f'✅ Canal creado: {channel_data["name"]}')
                        await asyncio.sleep(1.0)  # Mayor delay para evitar rate limiting
                    except Exception as e:
                        logger.error(f'❌ Error creando canal {channel_data["name"]}: {e}')
                
                await asyncio.sleep(1.5)  # Mayor delay entre categorías
            except Exception as e:
                logger.error(f'❌ Error en categoría {category_name}: {e}')

async def setup(bot):
    await bot.add_cog(ServerSetupCustom(bot))
