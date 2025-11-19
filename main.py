import discord
from discord.ext import commands
import os

# ---- USTAWIENIA
TICKET_CHANNEL_ID = 123456789012345678   # ID kanału gdzie ma być panel z ticketami
KATEGORIA_ID = 123456789012345678        # ID kategorii, w której będą tworzone tickety
ROLA_SUPPORT_ID = 123456789012345678     # ID roli supportu (która ma widzieć tickety)
KANAŁ_LOGI_ID = None  # opcjonalnie: ID kanału na logi zamkniętych ticketów

# -------------------- KONIEC USTAWIEŃ --------------------

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Embed i menu wyboru kategorii ticketa
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # timeout=None = wieczny

    @discord.ui.select(
        placeholder="Wybierz rodzaj ticketa...",
        options=[
            discord.SelectOption(label="Zgłoszenie gracza", description="Report na gracza", emoji="👮", value="report"),
            discord.SelectOption(label="Pomoc techniczna", description="Problem z serwerem/klientem", emoji="🛠️", value="support"),
            discord.SelectOption(label="Pytanie ogólne", description="Zwykłe pytanie do administracji", emoji="❓", value="pytanie"),
            discord.SelectOption(label="Skarga na moda", description="Tylko poważne sprawy", emoji="⚖️", value="skarga"),
            discord.SelectOption(label="Inne", description="Coś innego", emoji="📩", value="inne"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        kategoria = select.values[0]

        # Tworzenie kanału ticketa
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.get_role(ROLA_SUPPORT_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
        }

        kanal = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}-{kategoria}",
            category=interaction.guild.get_channel(KATEGORIA_ID),
            topic=f"Ticket użytkownika {interaction.user} | {kategoria}",
            overwrites=overwrites
        )

        # Embed w nowym kanale
        embed = discord.Embed(
            title="Nowy ticket!",
            description=f"{interaction.user.mention} otworzył ticket!\nKategoria: **{select.values[0]}**\n\nSupport zaraz się pojawi!",
            color=0x00ff00
        )
        embed.set_footer(text=f"ID użytkownika: {interaction.user.id}")

        close_button = discord.ui.Button(label="Zamknij ticket", style=discord.ButtonStyle.danger, emoji="🔒")
        
        async def close_callback(btn_interaction):
            await btn_interaction.response.send_message("Ticket zostanie zamknięty za 5 sekund...")
            await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=5))
            
            # Log do kanału
            if KANAŁ_LOGI_ID:
                log_channel = interaction.guild.get_channel(KANAŁ_LOGI_ID)
                await log_channel.send(f"Ticket zamknięty: `#{kanal.name}` przez {btn_interaction.user}")

            await kanal.delete()

        close_button.callback = close_callback

        view = discord.ui.View()
        view.add_item(close_button)

        await kanal.send(f"{interaction.user.mention} {interaction.guild.get_role(ROLA_SUPPORT_ID).mention}", embed=embed, view=view)

        await interaction.response.send_message(f"Ticket utworzony! ➜ {kanal.mention}", ephemeral=True)

# Start bota
@bot.event
async def on_ready():
    print(f'Bot zalogowany jako {bot.user}')
    
    # Dodaje widok 
    bot.add_view(TicketView())

    # Tworzenie panelu 
    # await create_panel()

async def create_panel():
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    await channel.purge()  # czyści kanał

    embed = discord.Embed(
        title="📮 SYSTEM TICKETÓW",
        description="Wybierz poniżej kategorię problemu, a utworzy się prywatny kanał tylko dla Ciebie i supportu!",
        color=0x2f3136
    )
    embed.set_image(url="https://i.imgur.com/2X6rT1I.gif")  # możesz zmienić na własny banner

    await channel.send(embed=embed, view=TicketView())

# Komenda do ręcznego wysłania panelu 
@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx):
    await ctx.message.delete()
    await create_panel()

# ----------------- URUCHOMIENIE -----------------
bot.run('TUTAJ_WKLEJ_TOKEN_BOTA')