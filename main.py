import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import datetime
from groq import Groq

# --- KONFIGURACJA PODSTAWOWA ---
# Twój token - nie zmieniaj go, jeśli bot ma działać
TOKEN = 'MTQ4MjMxNzkwNjk0NjU2MDE1MQ.G0frWR.AasrZKwF3WU0o5VU70K5iR1oM7YXLPvCpM0kAo'

# ID ról i kanałów z Twojego serwera
ID_ROLI_OBYWATEL = 1484166262413201480
ID_ROLI_NIEZWERYFIKOWANY = 1484166262857928755
ID_ROLI_ADMIN = 1484166256591634544
ID_KATEGORII_TICKETOW = 1484166476784078898
ID_KANALU_POWITAN = 1484166526922915861 
ID_KANALU_PROPOZYCJI = 1484166550595567696
ID_KANAL_LOGI_LSPD = 1484256738399096903 

# --- GRAFIKI (Twoje linki) ---
LINK_WERYFIKACJA = "https://media.discordapp.net/attachments/1482186127833305270/1484174809372950590/Weryfikacja.png"
LINK_TICKETY_GLOWNY = "https://media.discordapp.net/attachments/1482186127833305270/1484223924249301134/Nowy_projekt_-_2026-03-19T171530.917.png"
LINK_WNETRZE_TICKETU = "https://media.discordapp.net/attachments/1482186127833305270/1484224261257429063/Nowy_projekt_-_2026-03-19T171712.807.png"

# --- AI ---
client_ai = Groq(api_key='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')

# --- MODAL WERYFIKACJI ---
class CaptchaModal(discord.ui.Modal, title='Weryfikacja Echo RP'):
    def __init__(self):
        super().__init__()
        self.a, self.b = random.randint(1, 10), random.randint(1, 10)
        self.wynik = self.a + self.b
        self.ans = discord.ui.TextInput(label=f'Ile to {self.a} + {self.b}?', placeholder='Wpisz wynik tutaj...')
        self.add_item(self.ans)

    async def on_submit(self, interaction: discord.Interaction):
        if self.ans.value == str(self.wynik):
            r1 = interaction.guild.get_role(ID_ROLI_OBYWATEL)
            r2 = interaction.guild.get_role(ID_ROLI_NIEZWERYFIKOWANY)
            if r1: await interaction.user.add_roles(r1)
            if r2: await interaction.user.remove_roles(r2)
            await interaction.response.send_message("✅ Weryfikacja udana! Witamy na Echo RP.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Błędny wynik! Spróbuj ponownie.", ephemeral=True)

class VerificationView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Zweryfikuj się", style=discord.ButtonStyle.green, custom_id="verify_btn", emoji="🛡️")
    async def v_btn(self, interaction, button): await interaction.response.send_modal(CaptchaModal())

# --- SYSTEM TICKETÓW ---
class CloseTicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Zamknij Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket", emoji="🔒")
    async def c_btn(self, interaction: discord.Interaction, button):
        if interaction.user.guild_permissions.administrator or any(role.id == ID_ROLI_ADMIN for role in interaction.user.roles):
            await interaction.response.send_message("🔒 Zamykanie zgłoszenia za 3 sekundy...")
            await asyncio.sleep(3)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Tylko Administracja może zamykać tickety!", ephemeral=True)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='👑 Zarząd', value='Zarząd'),
            discord.SelectOption(label='🚓 Frakcja', value='Frakcja'),
            discord.SelectOption(label='❓ Pytanie', value='Pytanie'),
            discord.SelectOption(label='⚠️ Problem', value='Problem')
        ]
        super().__init__(placeholder='Wybierz powód zgłoszenia...', custom_id="ticket_select", options=options)

    async def callback(self, interaction):
        await interaction.response.defer(ephemeral=True)
        cat = interaction.guild.get_channel(ID_KATEGORII_TICKETOW)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
            interaction.guild.get_role(ID_ROLI_ADMIN): discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
        }
        chan = await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}", category=cat, overwrites=overwrites)
        embed = discord.Embed(title="🎫 NOWE ZGŁOSZENIE", description=f"Kategoria: **{self.values[0]}**\nCzekaj cierpliwie na pomoc.", color=discord.Color.blue())
        embed.set_image(url=LINK_WNETRZE_TICKETU)
        await chan.send(content=f"{interaction.user.mention} | <@&{ID_ROLI_ADMIN}>", embed=embed, view=CloseTicketView())
        await interaction.followup.send(f"✅ Twój ticket został otwarty: {chan.mention}", ephemeral=True)

class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# --- BOT SETUP ---
class EchoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerificationView())
        self.add_view(TicketLauncher())
        self.add_view(CloseTicketView())
        await self.tree.sync()

bot = EchoBot()

# --- KOMENDY SLASH (TABLET LSPD) ---
@bot.tree.command(name="kartoteka-dodaj", description="[LSPD] Dodaj obywatela do bazy danych")
async def k_dodaj(itn: discord.Interaction, obywatel: str, powod: str, grzywna: int):
    # Uprawnienia: Administrator lub Rola Admina
    if itn.user.guild_permissions.manage_messages or any(role.id == ID_ROLI_ADMIN for role in itn.user.roles):
        embed = discord.Embed(title="🚓 SYSTEM KARTOTEKI LSPD", color=discord.Color.blue(), timestamp=datetime.datetime.now())
        embed.add_field(name="👤 Obywatel", value=f"**{obywatel}**", inline=False)
        embed.add_field(name="📄 Powód wpisu", value=powod, inline=False)
        embed.add_field(name="💰 Kwota grzywny", value=f"{grzywna}$", inline=False)
        embed.set_footer(text=f"Wystawił funkcjonariusz: {itn.user.name}")
        
        log_chan = bot.get_channel(ID_KANAL_LOGI_LSPD)
        if log_chan:
            await log_chan.send(embed=embed)
        await itn.response.send_message(f"✅ Pomyślnie dodano wpis do kartoteki dla: **{obywatel}**.", ephemeral=True)
    else:
        await itn.response.send_message("❌ Nie masz uprawnień do korzystania z tabletu LSPD!", ephemeral=True)

# --- KOMENDY SETUPU ---
@bot.tree.command(name="setup-weryfikacja", description="Wysyła wiadomość z weryfikacją")
@app_commands.default_permissions(administrator=True)
async def setup_v(itn):
    embed = discord.Embed(title="🛡️ WERYFIKACJA ECHO RP", description="Aby uzyskać dostęp do serwera, kliknij przycisk poniżej i rozwiąż proste działanie.", color=discord.Color.green())
    embed.set_image(url=LINK_WERYFIKACJA)
    await itn.channel.send(embed=embed, view=VerificationView())
    await itn.response.send_message("✅ Panel weryfikacji wysłany.", ephemeral=True)

@bot.tree.command(name="setup-tickety", description="Wysyła wiadomość z ticketami")
@app_commands.default_permissions(administrator=True)
async def setup_t(itn):
    embed = discord.Embed(title="🎫 CENTRUM POMOCY", description="Potrzebujesz pomocy zarządu lub frakcji? Wybierz odpowiednią kategorię z listy poniżej.", color=discord.Color.blue())
    embed.set_image(url=LINK_TICKETY_GLOWNY)
    await itn.channel.send(embed=embed, view=TicketLauncher())
    await itn.response.send_message("✅ Panel ticketów wysłany.", ephemeral=True)

@bot.event
async def on_ready():
    print(f'>>> Echo Bot ONLINE jako {bot.user} <<<')

bot.run(TOKEN)
