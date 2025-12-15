import discord
from discord.ext import commands
from discord import ui
from config.server_config import SERVER_CONFIG, COLORS
import logging

logger = logging.getLogger(__name__)

class RoleSelect(ui.View):
    """Vista para seleccionar roles mediante dropdown"""
    
    def __init__(self, role_type: str):
        super().__init__(persistent=False)
        self.role_type = role_type
        self.add_item(RoleSelectDropdown(role_type))

class RoleSelectDropdown(ui.Select):
    """Dropdown para seleccionar roles"""
    
    def __init__(self, role_type: str):
        self.role_type = role_type
        
        # Obtener roles según el tipo
        role_dict = self.get_role_dict(role_type)
        
        options = []
        for key, role_data in role_dict.items():
            options.append(
                discord.SelectOption(
                    label=role_data['name'],
                    value=key,
                    emoji=role_data.get('emote', '🎮')
                )
            )
        
        super().__init__(
            placeholder=f'Selecciona tu {role_type}...',
            min_values=0,
            max_values=len(options),
            options=options
        )

    def get_role_dict(self, role_type):
        """Obtiene el diccionario de roles según el tipo"""
        if role_type == 'colors':
            return SERVER_CONFIG['color_roles']
        elif role_type == 'pronouns':
            return SERVER_CONFIG['pronoun_roles']
        elif role_type == 'age':
            return SERVER_CONFIG['age_roles']
        elif role_type == 'games':
            # Combinar todos los tiers de juegos
            all_games = {}
            for tier in range(1, 8):
                all_games.update(SERVER_CONFIG[f'games_tier{tier}'])
            return all_games
        return {}

    async def callback(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            member = interaction.user
            
            # Obtener todos los valores seleccionados
            selected_values = self.values
            
            # Obtener el diccionario de roles
            role_dict = self.get_role_dict(self.role_type)
            
            # Primero, remover todos los roles de este tipo
            for role_key, role_data in role_dict.items():
                role = discord.utils.get(guild.roles, name=role_data['name'])
                if role and role in member.roles:
                    await member.remove_roles(role)
            
            # Luego, añadir los nuevos roles seleccionados
            for value in selected_values:
                if value in role_dict:
                    role_data = role_dict[value]
                    role = discord.utils.get(guild.roles, name=role_data['name'])
                    if role:
                        await member.add_roles(role)
            
            role_names = ', '.join([role_dict[v]['name'] for v in selected_values]) if selected_values else 'ninguno'
            
            await interaction.response.send_message(
                f'✅ ¡Tus roles han sido actualizados! Roles: {role_names}',
                ephemeral=True
            )
            logger.info(f'{member} actualizó sus {self.role_type}: {role_names}')
            
        except discord.Forbidden:
            logger.warning(f'No se pudieron actualizar los roles para {member} debido a permisos insuficientes.')
            await interaction.response.send_message(
                '❌ No tengo permisos para gestionar roles. Por favor, contacta a un administrador.',
                ephemeral=True
            )
        except discord.HTTPException as e:
            logger.error(f'Error HTTP al actualizar roles para {member}: {e}')
            await interaction.response.send_message(
                f'❌ Ocurrió un error al comunicarme con Discord. Inténtalo de nuevo más tarde. ({e})',
                ephemeral=True
            )
        except Exception as e:
            logger.error(f'Error inesperado actualizando roles para {member}: {e}')
            await interaction.response.send_message(
                f'❌ Ocurrió un error inesperado al actualizar tus roles: {e}',
                ephemeral=True
            )

class RoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='role_menu')
    @commands.has_permissions(administrator=True)
    async def role_menu(self, ctx, role_type: str = None):
        """Crea un menú de selección de roles.
        Los tipos disponibles son: colors, pronouns, age, games.
        Uso: !role_menu <tipo>
        Ejemplo: !role_menu colors
        """
        
        if not role_type or role_type.lower() not in ['colors', 'pronouns', 'age', 'games']:
            await ctx.send('❌ Tipo de rol inválido. Usa: colors, pronouns, age o games')
            return

        role_type = role_type.lower()
        
        # Crear embeds y vistas según el tipo
        if role_type == 'colors':
            embed = discord.Embed(
                title='🌈 Selecciona tu Color',
                description='Elige el color que te representa UwU',
                color=COLORS['primary']
            )
            embed.set_footer(text='Puedes seleccionar múltiples colores')
            
        elif role_type == 'pronouns':
            embed = discord.Embed(
                title='👤 Selecciona tus Pronombres',
                description='Elige los pronombres con los que te sientes cómodo/a',
                color=COLORS['primary']
            )
            embed.set_footer(text='Solo puedes seleccionar uno')
            
        elif role_type == 'age':
            embed = discord.Embed(
                title='🧒 Selecciona tu Rango de Edad',
                description='Elige tu rango de edad',
                color=COLORS['primary']
            )
            embed.set_footer(text='Solo puedes seleccionar uno')
            
        elif role_type == 'games':
            embed = discord.Embed(
                title='🎮 Selecciona tus Juegos Favoritos',
                description='Elige los juegos que juegas',
                color=COLORS['primary']
            )
            embed.set_footer(text='Puedes seleccionar múltiples juegos')
        
        view = RoleSelect(role_type)
        await ctx.send(embed=embed, view=view)

    @commands.command(name='send_role_embeds')
    @commands.has_permissions(administrator=True)
    async def send_role_embeds(self, ctx):
        """Envía todos los embeds de selección de roles a los canales correspondientes"""
        
        guild = ctx.guild
        
        # Canal de selección de roles
        select_roles_channel = discord.utils.get(guild.text_channels, name=SERVER_CONFIG['text_channels']['select_roles']['name'])
        if select_roles_channel:
            embed = discord.Embed(
                title='🎨 Selecciona tus Roles',
                description='Aquí puedes seleccionar los roles que deseas en el servidor. '
                           'Los roles de staff no están disponibles aquí.',
                color=COLORS['primary']
            )
            bot_messages = [message async for message in select_roles_channel.history(limit=10) if message.author == self.bot.user]
            if bot_messages:
                await select_roles_channel.delete_messages(bot_messages)
            await select_roles_channel.send(embed=embed)
        
        # Canal de colores
        colors_channel = discord.utils.get(guild.text_channels, name=SERVER_CONFIG['text_channels']['select_colors']['name'])
        if colors_channel:
            embed = discord.Embed(
                title='🌈 Selecciona tu Color Favorito',
                description='Elige el color que mejor te representa UwU',
                color=COLORS['primary']
            )
            view = RoleSelect('colors')
            bot_messages = [message async for message in colors_channel.history(limit=10) if message.author == self.bot.user]
            if bot_messages:
                await colors_channel.delete_messages(bot_messages)
            await colors_channel.send(embed=embed, view=view)
        
        # Canal de pronombres
        pronouns_channel = discord.utils.get(guild.text_channels, name=SERVER_CONFIG['text_channels']['select_pronouns']['name'])
        if pronouns_channel:
            embed = discord.Embed(
                title='👤 Selecciona tus Pronombres',
                description='Elige los pronombres con los que te sientes cómodo/a',
                color=COLORS['primary']
            )
            view = RoleSelect('pronouns')
            bot_messages = [message async for message in pronouns_channel.history(limit=10) if message.author == self.bot.user]
            if bot_messages:
                await pronouns_channel.delete_messages(bot_messages)
            await pronouns_channel.send(embed=embed, view=view)
        
        # Canal de edad
        age_channel = discord.utils.get(guild.text_channels, name=SERVER_CONFIG['text_channels']['select_age']['name'])
        if age_channel:
            embed = discord.Embed(
                title='🧒 Selecciona tu Rango de Edad',
                description='Elige tu rango de edad',
                color=COLORS['primary']
            )
            view = RoleSelect('age')
            bot_messages = [message async for message in age_channel.history(limit=10) if message.author == self.bot.user]
            if bot_messages:
                await age_channel.delete_messages(bot_messages)
            await age_channel.send(embed=embed, view=view)
        
        # Canal de juegos
        games_channel = discord.utils.get(guild.text_channels, name=SERVER_CONFIG['text_channels']['select_games']['name'])
        if games_channel:
            embed = discord.Embed(
                title='🎮 Selecciona tus Juegos Favoritos',
                description='Elige los juegos que más juegas',
                color=COLORS['primary']
            )
            view = RoleSelect('games')
            bot_messages = [message async for message in games_channel.history(limit=10) if message.author == self.bot.user]
            if bot_messages:
                await games_channel.delete_messages(bot_messages)
            await games_channel.send(embed=embed, view=view)
        
        await ctx.send('✅ Menús de selección enviados a todos los canales correctamente UwU')

async def setup(bot):
    await bot.add_cog(RoleCog(bot))
