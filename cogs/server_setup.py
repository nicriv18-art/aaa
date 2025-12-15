import discord
from discord.ext import commands
import logging
import asyncio
from config.server_config import SERVER_CONFIG, COLORS

logger = logging.getLogger(__name__)

class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _create_with_retry(self, coro, item_name, max_retries=5, base_delay=1):
        # Nota: No se puede reintentar una corutina ya instanciada ('await coro' la consume).
        # Además, discord.py maneja los rate limits (429) internamente.
        try:
            return await coro
        except Exception as e:
            logger.error(f"Fallo al crear {item_name}: {e}")
            raise e

    async def cleanup_server(self, guild):
        """Elimina TODOS los canales y roles para empezar de cero (de forma segura)"""
        try:
            # Eliminar todos los canales (texto, voz y categorías)
            channels_deleted = 0
            for channel in list(guild.channels):
                try:
                    await channel.delete()
                    channels_deleted += 1
                    logger.info(f'Canal eliminado: {channel.name}')
                    await asyncio.sleep(1.0)  # Evitar rate limiting
                except Exception as e:
                    logger.warning(f'⚠️ Advertencia eliminando canal {channel.name}: {e}')
            
            # Eliminar todos los foros
            forums_deleted = 0
            for forum in list(guild.forums):
                try:
                    await forum.delete()
                    forums_deleted += 1
                    logger.info(f'Foro eliminado: {forum.name}')
                    await asyncio.sleep(1.0)  # Evitar rate limiting
                except Exception as e:
                    logger.warning(f'⚠️ Advertencia eliminando foro: {e}')
            
            # Proteger roles importantes
            protected_roles = {
                guild.default_role,  # @everyone
                guild.me.top_role,   # El rol del bot
            }
            
            # Añadir todos los roles del bot a protected
            for role in guild.me.roles:
                protected_roles.add(role)
            
            # Eliminar SOLO los roles de usuario personalizados
            roles_deleted = 0
            for role in sorted(list(guild.roles), key=lambda r: r.position, reverse=True):
                # Proteger roles especiales
                if role in protected_roles:
                    logger.info(f'🔒 Rol protegido: {role.name}')
                    continue
                
                # Proteger roles de integraciones
                if role.managed:
                    logger.info(f'🔒 Rol de integración: {role.name}')
                    continue
                
                try:
                    await role.delete(reason='Limpieza de servidor automática')
                    roles_deleted += 1
                    logger.info(f'✅ Rol eliminado: {role.name}')
                    await asyncio.sleep(0.7)  # Evitar rate limiting
                except Exception as e:
                    logger.warning(f'⚠️ No se pudo eliminar {role.name}: {e}')
            
            logger.info(f'Cleanup: {channels_deleted} canales, {forums_deleted} foros, {roles_deleted} roles')
            
        except Exception as e:
            logger.error(f'Error crítico durante cleanup: {e}')

    @commands.command(name='eliminar_todo', help='Elimina canales y roles para reiniciar el servidor.')
    @commands.has_permissions(administrator=True)
    async def eliminar_todo_command(self, ctx):
        guild = ctx.guild
        if not guild:
            await ctx.send("Este comando solo puede ser usado en un servidor.")
            return

        await ctx.send("Iniciando la limpieza completa del servidor, esto puede tardar...")
        await self.cleanup_server(guild)
        await ctx.send("Limpieza del servidor completada.")

    @commands.command(name='crear_canales', help='Crea las categorías y canales del servidor.')
    @commands.has_permissions(administrator=True)
    async def crear_canales_command(self, ctx):
        guild = ctx.guild
        if not guild:
            await ctx.send("Este comando solo puede ser usado en un servidor.")
            return

        # Verificación de permisos del BOT
        if not guild.me.guild_permissions.manage_channels:
            await ctx.send("❌ **ERROR DE PERMISOS:** No tengo permiso para gestionar canales.\n"
                           "Activa **Administrador** o **Gestionar Canales** en mi rol.")
            return

        status_msg = await ctx.send("🔄 **Iniciando la creación de canales...**\n(Esto puede tardar un poco)")
        
        try:
            count = await self.create_channels(guild)
            await status_msg.edit(content=f"✅ **Creación de canales finalizada.**\nSe han creado/verificado {count} canales.")
        except Exception as e:
            await ctx.send(f"❌ Ocurrió un error inesperado al crear canales: {str(e)}")

    @commands.command(name='crear_roles', help='Crea los roles predefinidos en el servidor.')
    @commands.has_permissions(administrator=True)
    async def crear_roles_command(self, ctx):
        guild = ctx.guild
        if not guild:
            await ctx.send("Este comando solo puede ser usado en un servidor.")
            return

        # Verificación de permisos del BOT
        if not guild.me.guild_permissions.manage_roles:
            await ctx.send("❌ **ERROR CRÍTICO:** No tengo permiso para gestionar roles.\n"
                           "Por favor, ve a la configuración del servidor -> Roles -> Fiscord Bot (o el rol del bot) -> Permisos -> Activa **Administrador** o **Gestionar Roles**.")
            return

        status_msg = await ctx.send("🔄 **Iniciando la creación de roles...**\n(Esto puede tardar un poco para evitar límites de Discord)")
        
        try:
            count = await self.create_roles(guild, status_msg)
            await status_msg.edit(content=f"✅ **Creación de roles finalizada.**\nSe han creado/verificado {count} roles.")
        except Exception as e:
            await ctx.send(f"❌ Ocurrió un error inesperado: {str(e)}")

    @commands.command(name='crear_permisos', help='Configura los permisos profesionales en el servidor.')
    @commands.has_permissions(administrator=True)
    async def crear_permisos_command(self, ctx):
        guild = ctx.guild
        if not guild:
            await ctx.send("Este comando solo puede ser usado en un servidor.")
            return

        await ctx.send("Iniciando la configuración de permisos...")
        await self.setup_permissions(guild)
        await ctx.send("Configuración de permisos finalizada.")

    async def create_roles(self, guild, status_msg=None):
        """Crea TODOS los roles necesarios (profesional y jerárquico)"""
        try:
            all_roles = {
                **SERVER_CONFIG['staff_roles'],
                **SERVER_CONFIG['user_roles'],
                **SERVER_CONFIG['color_roles'],
                **SERVER_CONFIG['pronoun_roles'],
                **SERVER_CONFIG['age_roles'],
                **SERVER_CONFIG['games_tier1'],
                **SERVER_CONFIG['games_tier2'],
                **SERVER_CONFIG['games_tier3'],
                **SERVER_CONFIG['games_tier4'],
                **SERVER_CONFIG['games_tier5'],
                **SERVER_CONFIG['games_tier6'],
                **SERVER_CONFIG['games_tier7'],
            }
            
            created_roles = 0
            failed_roles = []
            existing_roles = []
            
            # Crear roles por categoría en orden de jerarquía
            categories = [
                ('Color Roles', SERVER_CONFIG['color_roles']),
                ('Staff Roles', SERVER_CONFIG['staff_roles']),
                ('User Roles', SERVER_CONFIG['user_roles']),
                ('Age Roles', SERVER_CONFIG['age_roles']),
                ('Pronoun Roles', SERVER_CONFIG['pronoun_roles']),
                ('Games Tier 1', SERVER_CONFIG['games_tier1']),
                ('Games Tier 2', SERVER_CONFIG['games_tier2']),
                ('Games Tier 3', SERVER_CONFIG['games_tier3']),
                ('Games Tier 4', SERVER_CONFIG['games_tier4']),
                ('Games Tier 5', SERVER_CONFIG['games_tier5']),
                ('Games Tier 6', SERVER_CONFIG['games_tier6']),
                ('Games Tier 7', SERVER_CONFIG['games_tier7']),
            ]
            
            total_categories = len(categories)
            current_cat = 0

            for category_name, roles_dict in categories:
                current_cat += 1
                if status_msg and current_cat % 2 == 0:
                    try:
                        await status_msg.edit(content=f"🔄 **Creando roles...**\nProcesando categoría {current_cat}/{total_categories}: {category_name}")
                    except:
                        pass

                for role_key, role_data in roles_dict.items():
                    try:
                        # Verificar si el rol ya existe
                        existing_role = discord.utils.get(guild.roles, name=role_data['name'])
                        if existing_role:
                            existing_roles.append(role_data['name'])
                            logger.info(f'⏭️ Rol ya existe: {role_data["name"]} ({category_name})')
                            continue
                        
                        role = await self._create_with_retry(
                            guild.create_role(
                                name=role_data['name'],
                                color=discord.Color(role_data.get('color', 0xFF69B4)),
                                hoist=role_data.get('hoist', False),
                                mentionable=role_data.get('mentionable', False),
                                reason=f'Rol de {category_name} - Configuración automática'
                            ),
                            f"rol {role_data['name']}"
                        )
                        created_roles += 1
                        logger.info(f'✅ Rol creado: {role.name} ({category_name})')
                        await asyncio.sleep(1.0)
                    except discord.Forbidden:
                        if status_msg:
                            await status_msg.channel.send(f"❌ **Error de permisos** al intentar crear el rol '{role_data['name']}'. Verifica que mi rol esté por encima de los roles que intento gestionar.")
                        failed_roles.append(role_data['name'])
                    except Exception as e:
                        failed_roles.append(role_data['name'])
                        logger.error(f'❌ Error creando rol {role_data["name"]}: {e}')
            
            logger.info(f'Roles: {created_roles} creados, {len(existing_roles)} ya existentes, {len(failed_roles)} fallados')
            return created_roles
            
        except Exception as e:
            logger.error(f'Error crítico creando roles: {e}')
            raise e

    async def create_channels(self, guild):
        """Crea categorías y canales CON PERMISOS PROFESIONALES"""
        try:
            # Obtener roles importantes
            admin_role = discord.utils.get(guild.roles, name=SERVER_CONFIG['staff_roles']['admin']['name'])
            mod_role = discord.utils.get(guild.roles, name=SERVER_CONFIG['staff_roles']['moderator']['name'])
            member_role = discord.utils.get(guild.roles, name=SERVER_CONFIG['user_roles']['miembro']['name'])
            everyone_role = guild.default_role
            
            created_channels = 0
            
            # Estructura de categorías y canales con permisos
            structure = {
                '📢 ┃ INFORMACIÓN': [
                    ('📋-bienvenida', '✨ Bienvenida al servidor kawaii ✨', 'texto', {'view': True, 'send': False}),
                    ('📝-reglas', '📋 Reglas y normativa del servidor', 'texto', {'view': True, 'send': False}),
                    ('📢-anuncios', '🎺 Anuncios importantes y actualizaciones', 'texto', {'view': True, 'send': False}),
                ],
                '💬 ┃ GENERAL': [
                    ('✨-general', '💬 Chat general del servidor', 'texto', {'view': True, 'send': True}),
                    ('🎤-voz-general', '🎤 Canal de voz general', 'voz', {'view': True}),
                    ('🔊-stream', '🎮 Transmisiones y streams en vivo', 'voz', {'view': True}),
                ],
                '🎮 ┃ VIDEOJUEGOS': [
                    ('🎮-gaming', '🎮 Hablar de videojuegos', 'texto', {'view': True, 'send': True}),
                    ('⚔️-multijugador', '⚔️ Partidas multijugador', 'texto', {'view': True, 'send': True}),
                    ('🏆-competencias', '🏆 Competencias y torneos', 'texto', {'view': True, 'send': True}),
                    ('🎯-voz-gaming', '🎮 Voz para gaming', 'voz', {'view': True}),
                ],
                '🎨 ┃ COMUNIDAD': [
                    ('🎨-arte', '🎨 Comparte tu arte y creatividad', 'texto', {'view': True, 'send': True}),
                    ('📸-fotos', '📸 Fotos bonitas y paisajes', 'texto', {'view': True, 'send': True}),
                    ('🐾-animales', '🐾 Fotos de animales adorables', 'texto', {'view': True, 'send': True}),
                    ('🎥-clips', '🎥 Clips y videos cortos', 'texto', {'view': True, 'send': True}),
                    ('😄-face-reveal', '😄 Face reveal de la comunidad', 'texto', {'view': True, 'send': True}),
                    ('😂-memes', '😂 Memes y contenido divertido', 'texto', {'view': True, 'send': True}),
                    ('🎵-música', '🎵 Recomendaciones de música', 'texto', {'view': True, 'send': True}),
                ],
                '📝 ┃ PRESENTACIONES': [
                    ('👋-presentaciones', '👋 Preséntate a la comunidad', 'texto', {'view': True, 'send': True}),
                ],
                '🎫 ┃ SOPORTE': [
                    ('🎫-tickets', '🎫 Sistema de tickets de soporte', 'texto', {'view': True, 'send': True}),
                ],
                '🔧 ┃ STAFF': [
                    ('📋-logs', '📋 Registro de eventos y logs', 'texto', {'staff_only': True}),
                    ('💬-staff-chat', '💬 Chat privado del staff', 'texto', {'staff_only': True}),
                    ('🔊-voz-staff', '🔊 Voz para staff', 'voz', {'staff_only': True}),
                ],
            }
            
            # Crear categorías y canales
            for category_name, channels_list in structure.items():
                try:
                    # Verificar si la categoría ya existe
                    existing_category = discord.utils.get(guild.categories, name=category_name)
                    if existing_category:
                        logger.info(f'⚠️ Categoría ya existe: {category_name}')
                        category = existing_category
                    else:
                        # Crear categoría
                        category = await guild.create_category(
                            category_name,
                            reason='Configuración automática del servidor'
                        )
                    
                    # Configurar permisos de la categoría
                    everyone_perms = discord.PermissionOverwrite(view_channel=False)
                    await category.edit(overwrites={everyone_role: everyone_perms})
                    
                    logger.info(f'✅ Categoría: {category_name}')
                    
                    for channel_name, description, channel_type, perms_config in channels_list:
                        try:
                            existing_channel = discord.utils.get(guild.channels, name=channel_name)
                            if existing_channel:
                                channel = existing_channel
                                if channel.category != category:
                                    await channel.edit(category=category, reason='Reorganización automática de canales')
                                logger.info(f'⚠️ Canal ya existía, ajustando permisos y categoría: {channel_name}')
                            else:
                                if channel_type == 'texto':
                                    channel = await self._create_with_retry(
                                        guild.create_text_channel(
                                            name=channel_name,
                                            category=category,
                                            topic=description,
                                            reason='Configuración automática'
                                        ),
                                        f"canal de texto {channel_name}"
                                    )
                                else:
                                    channel = await self._create_with_retry(
                                        guild.create_voice_channel(
                                            name=channel_name,
                                            category=category,
                                            reason='Configuración automática'
                                        ),
                                        f"canal de voz {channel_name}"
                                    )
                                
                                created_channels += 1
                                logger.info(f'✅ Canal creado: {channel_name} con permisos')

                            overwrites = await self._get_channel_permissions(
                                guild, perms_config
                            )
                            try:
                                await channel.edit(overwrites=overwrites)
                            except discord.Forbidden:
                                logger.warning(f"No se pudieron establecer permisos para {channel_name} debido a jerarquía de roles.")

                        except Exception as e:
                            logger.error(f'❌ Error creando canal {channel_name}: {e}')
                            
                except Exception as e:
                    logger.error(f'❌ Error creando categoría {category_name}: {e}')
            
            logger.info(f'Canales: {created_channels} creados correctamente')
            return created_channels
            
        except Exception as e:
            logger.error(f'Error crítico creando canales: {e}')
            raise e

    async def _get_channel_permissions(self, guild, perms_config):
        """Genera permisos profesionales para un canal"""
        overwrites = {}
        everyone_role = guild.default_role
        admin_role = discord.utils.get(guild.roles, name=SERVER_CONFIG['staff_roles']['admin']['name'])
        mod_role = discord.utils.get(guild.roles, name=SERVER_CONFIG['staff_roles']['moderator']['name'])
        member_role = discord.utils.get(guild.roles, name=SERVER_CONFIG['user_roles']['miembro']['name'])
        
        # Permiso base: bloquear @everyone
        overwrites[everyone_role] = discord.PermissionOverwrite(
            view_channel=perms_config.get('staff_only', False)  # False si es público
        )
        
        # Admin siempre puede ver y administrar
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_messages=True,
                manage_channels=True,
                manage_roles=True,
                manage_webhooks=True,
                connect=True,
                speak=True,
                move_members=True,
                mute_members=True,
                deafen_members=True,
                mention_everyone=True
            )
        
        # Co-Owner: Acceso casi total (igual que Owner pero sin manage_roles)
        owner_role = discord.utils.get(guild.roles, name='👑 Owner')
        coowner_role = discord.utils.get(guild.roles, name='👸 Co-Owner')
        if coowner_role:
            overwrites[coowner_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_messages=True,
                manage_channels=True,
                manage_webhooks=True,
                connect=True,
                speak=True,
                move_members=True,
                mute_members=True,
                deafen_members=True,
                mention_everyone=False
            )
        
        # Mod puede moderar
        if mod_role and not perms_config.get('staff_only', False):
            overwrites[mod_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_messages=True
            )
        
        # Miembros pueden ver según config
        if member_role and not perms_config.get('staff_only', False):
            can_send = perms_config.get('send', False)
            overwrites[member_role] = discord.PermissionOverwrite(
                view_channel=perms_config.get('view', True),
                send_messages=can_send,
                read_message_history=True
            )
        
        return overwrites

    async def create_forums(self, guild):
        """Crea foros para discusiones temáticas"""
        try:
            forums_config = {
                '📚 ┃ RECURSOS': '📚 Comparte recursos, tutoriales y material educativo',
                '❓ ┃ PREGUNTAS': '❓ Haz preguntas y obtén respuestas de la comunidad',
                '💡 ┃ SUGERENCIAS': '💡 Sugiere ideas para mejorar el servidor',
                '🐛 ┃ REPORTES': '🐛 Reporta problemas técnicos y bugs encontrados',
            }
            
            created_forums = 0
            for forum_name, description in forums_config.items():
                try:
                    forum = await guild.create_forum(
                        name=forum_name,
                        description=description,
                        reason='Configuración automática del servidor'
                    )
                    created_forums += 1
                    logger.info(f'✅ Foro creado: {forum_name}')
                    await asyncio.sleep(0.3)  # Evitar rate limiting
                except Exception as e:
                    logger.error(f'❌ Error creando foro {forum_name}: {e}')
            
            logger.info(f'Foros: {created_forums} creados')
            
        except Exception as e:
            logger.error(f'Error creando foros: {e}')

    async def setup_permissions(self, guild):
        """Configura permisos profesionales por canal y rol - JERARQUÍA PROFESIONAL"""
        try:
            
            # Obtener roles por jerarquía (NUEVO: Owner y Co-Owner)
            owner_role = discord.utils.get(guild.roles, name='👑 Owner')
            coowner_role = discord.utils.get(guild.roles, name='👸 Co-Owner')
            admin_role = discord.utils.get(guild.roles, name='💎 Admin Rubius')
            mod_role = discord.utils.get(guild.roles, name='🌸 Mod Kawaii')
            helper_role = discord.utils.get(guild.roles, name='✨ Helper Cute')
            member_role = discord.utils.get(guild.roles, name='🎀 Miembro Cute')
            everyone_role = guild.default_role
            
            channels_fixed = 0
            
            # Configurar permisos para todos los canales
            for channel in guild.text_channels + guild.voice_channels:
                try:
                    # Determinar tipo de canal por nombre
                    channel_name = channel.name.lower()
                    is_staff_channel = 'staff' in channel_name or 'logs' in channel_name
                    is_read_only = 'bienvenida' in channel_name or 'reglas' in channel_name or 'anuncios' in channel_name
                    
                    overwrites = {}
                    
                    # 1. @everyone: BLOQUEADO en TODOS los canales
                    overwrites[everyone_role] = discord.PermissionOverwrite(
                        view_channel=False,
                        send_messages=False,
                        connect=False,
                        speak=False
                    )
                    
                    # 2. OWNER: Acceso TOTAL a TODO (máxima jerarquía)
                    if owner_role:
                        overwrites[owner_role] = discord.PermissionOverwrite(
                            view_channel=True,
                            send_messages=True,
                            manage_messages=True,
                            manage_channels=True,
                            manage_roles=True,
                            manage_webhooks=True,
                            connect=True,
                            speak=True,
                            move_members=True,
                            mute_members=True,
                            deafen_members=True,
                            mention_everyone=True
                        )
                    
                    # 3. CO-OWNER: Acceso casi total (igual que Owner pero sin manage_roles)
                    if coowner_role:
                        overwrites[coowner_role] = discord.PermissionOverwrite(
                            view_channel=True,
                            send_messages=True,
                            manage_messages=True,
                            manage_channels=True,
                            manage_webhooks=True,
                            connect=True,
                            speak=True,
                            move_members=True,
                            mute_members=True,
                            deafen_members=True,
                            mention_everyone=False
                        )
                    
                    # 4. ADMIN: Acceso administración de contenido
                    if admin_role:
                        if is_staff_channel:
                            # Admin SI accede a staff channels
                            overwrites[admin_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                manage_messages=True,
                                manage_channels=True,
                                connect=True,
                                speak=True,
                                move_members=True,
                                mute_members=True
                            )
                        else:
                            # Admin acceso normal a otros canales
                            overwrites[admin_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                manage_messages=True,
                                manage_channels=True,
                                connect=True,
                                speak=True,
                                move_members=True
                            )
                    
                    # 4. MOD: Solo moderación (no puede editar canales, excepto staff)
                    if mod_role:
                        if is_staff_channel:
                            # Mod SÍ accede a staff channels
                            overwrites[mod_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                manage_messages=True,
                                connect=True,
                                speak=True,
                                mute_members=True
                            )
                        else:
                            # Mod acceso a otros canales
                            overwrites[mod_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                manage_messages=True,
                                connect=True,
                                speak=True
                            )
                    
                    # 5. HELPER: Acceso limitado (solo lectura en staff, participación en otros)
                    if helper_role:
                        if is_staff_channel:
                            # Helper accede pero solo lectura
                            overwrites[helper_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=False,
                                read_message_history=True,
                                connect=False
                            )
                        else:
                            # Helper acceso normal
                            overwrites[helper_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                read_message_history=True,
                                connect=True,
                                speak=True
                            )
                    
                    # 6. MIEMBROS: Acceso según tipo de canal
                    if member_role:
                        if is_staff_channel:
                            # Miembros NO acceden a staff channels
                            overwrites[member_role] = discord.PermissionOverwrite(
                                view_channel=False
                            )
                        elif is_read_only:
                            # Solo lectura en canales de información
                            overwrites[member_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=False,
                                read_message_history=True,
                                connect=False
                            )
                        else:
                            # Acceso completo (lectura-escritura) en otros canales
                            overwrites[member_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                read_message_history=True,
                                connect=True,
                                speak=True
                            )
                    
                    # Aplicar permisos
                    await channel.edit(overwrites=overwrites, reason='Configuración de permisos profesionales')
                    channels_fixed += 1
                    logger.info(f'✅ Permisos configurados: {channel.name}')
                    await asyncio.sleep(0.1)  # Evitar rate limiting
                    
                except Exception as e:
                    logger.error(f'❌ Error configurando permisos en {channel.name}: {e}')
            
            # Configurar permisos para foros
            for forum in guild.forums:
                try:
                    overwrites = {
                        everyone_role: discord.PermissionOverwrite(view_channel=False)
                    }
                    if owner_role:
                        overwrites[owner_role] = discord.PermissionOverwrite(view_channel=True)
                    if admin_role:
                        overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)
                    if mod_role:
                        overwrites[mod_role] = discord.PermissionOverwrite(view_channel=True)
                    if helper_role:
                        overwrites[helper_role] = discord.PermissionOverwrite(view_channel=True)
                    if member_role:
                        overwrites[member_role] = discord.PermissionOverwrite(view_channel=True)
                    
                    await forum.edit(overwrites=overwrites, reason='Configuración de permisos')
                    await asyncio.sleep(0.1)  # Evitar rate limiting
                except Exception as e:
                    logger.error(f'Error en foro {forum.name}: {e}')
            
            logger.info(f'✅ Permisos profesionales: {channels_fixed} canales configurados correctamente')
            
        except Exception as e:
            logger.error(f'Error crítico en permisos: {e}')

async def setup(bot):
    await bot.add_cog(ServerSetup(bot))
