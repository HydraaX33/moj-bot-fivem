import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import datetime
from groq import Groq

# --- KONFIGURACJA PODSTAWOWA ---
TOKEN = 'MTQ4MjMxNzkwNjk0NjU2MDE1MQ.G0frWR.AasrZKwF3WU0o5VU70K5iR1oM7YXLPvCpM0kAo'
ID_ROLI_OBYWATEL = 1484166262413201480
ID_ROLI_NIEZWERYFIKOWANY = 1484166262857928755
ID_ROLI_ADMIN = 1484166256591634544
ID_KATEGORII_TICKETOW = 1484166476784078898
ID_KANALU_POWITAN = 1484166526922915861 
ID_KANALU_PROPOZYCJI = 1484166550595567696

# --- KONFIGURACJA STATYSTYK ---
ID_SERWERA = 1482186127221035008 
ID_KANAL_GRACZE = 1484255325447262348
ID_KANAL_BOTY = 1484255547808157787
ID_KANAL_DATA = 1484256738399096903
ID_KANAL_GODZINA = 1484256800005029908

# --- LINKI DO GRAFIK ---
LINK_POWITANIE = "https://cdn.discordapp.com/attachments/1482186127833305270/1484260515554398231/witaj.png"
LINK_POZEGNANIE = "https://media.discordapp.net/attachments/1482186127833305270/1484174809372950590/Weryfikacja.png"
LINK_WERYFIKACJA = "https://media.discordapp.net/attachments/1482186127833305270/1484174809372950590/Weryfikacja.png"
LINK_TICKETY_GLOWNY = "https://media.discordapp.net/attachments/1482186127833305270/1484223924249301134/Nowy_projekt_-_2026-03-19T171530.917.png?ex=69bd72bf&is=69bc213f&hm=77848e6f1487fd15cd1b2af6b9e71712c4dcd3d9a8f589edbbecc1a5f9c8d5d0&=&format=webp&quality=lossless"
LINK_WNETRZE_TICKETU = "https://media.discordapp.net/attachments/1482186127833305270/1484224261257429063/Nowy_projekt_-_2026-03-19T171712.807.png?ex=69bd730f&is=69bc218f&hm=4626de470cda97c11773661e2ad27eff0eb443ecedd9d78d5c6bba20619de90a&=&format=webp&quality=lossless"

# --- AI ---
client_ai = Groq(api_key='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')
AI_PROMPT = "Jesteś asystentem Echo RP. Odpowiadaj krótko i w klimacie Roleplay."

# --- WERYFIKACJA ---
class CaptchaModal(discord.ui.Modal, title='Weryfikacja Echo RP'):
    def __init__(self):
        super().__init__()
        self.a, self.b = random.randint(1, 10), random.randint(1, 10)
        self.wynik = self.a + self.b
        self.ans = discord.ui.TextInput(label=f'Ile to {self.a} + {self.b}?', placeholder='Wynik...')
        self.add_item(self.ans)

    async def on_submit(self, interaction: discord.Interaction):
        if self.ans.value == str(self.wynik):
            r1, r2 = interaction.guild.get_role(ID_ROLI_OBYWATEL), interaction.guild.get_role(ID_ROLI_NIEZWERYFIKOWANY)
            if r1: await interaction.user.add_roles(r1)
            if r2: await interaction.user.remove_roles(r2)
            await interaction.response.send_message("✅ Witamy na Echo RP!", ephemeral=True)
        else: await interaction.response.send_message("❌ Błąd!", ephemeral=True)

class VerificationView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Weryfikacja", style=discord.ButtonStyle.green, custom_id="v_v6", emoji="🛡️")
    async def v_btn(self, interaction, button): await interaction.response.send_modal(CaptchaModal())

# --- TICKETY ---
class CloseTicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Zamknij Ticket", style=discord.ButtonStyle.red, custom_id="c_t_v6", emoji="🔒")
    async def c_btn(self, interaction, button):
        await interaction.response.send_message("🔒 Zamykanie kanału za 3 sekundy...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Sprawa Zarządu', description='Prywatna sprawa do wyższej administracji', value='Zarząd', emoji="👑"),
            discord.SelectOption(label='Sprawa Frakcji', description='Problemy lub pytania dotyczące frakcji', value='Frakcja', emoji="🚓"),
            discord.SelectOption(label='Pytanie', description='Masz proste pytanie dotyczące serwera?', value='Pytanie', emoji="❓"),
            discord.SelectOption(label='Problem', description='Zgłoś błąd lub problem techniczny', value='Problem', emoji="⚠️")
        ]
        super().__init__(placeholder='Wybierz kategorię zgłoszenia...', custom_id="t_s_v6", options=options)

    async def callback(self, interaction):
        await interaction.response.defer(ephemeral=True)
        category = interaction.guild.get_channel(ID_KATEGORII_TICKETOW)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
            interaction.guild.get_role(ID_ROLI_ADMIN): discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
        }
        chan = await interaction.guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
        
        embed = discord.Embed(
            title="🎫 ZGŁOSZENIE PRZYJĘTE",
            description=f"Witaj {interaction.user.mention}!\n\nWybrana kategoria: **{self.values[0]}**\nOpisz dokładnie swój problem, a administracja zajmie się zgłoszeniem.",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        embed.set_image(url=LINK_WNETRZE_TICKETU)
        
        await chan.send(content=f"{interaction.user.mention} | <@&{ID_ROLI_ADMIN}>", embed=embed, view=CloseTicketView())
        await interaction.followup.send(f"✅ Twój ticket został otwarty: {chan.mention}", ephemeral=True)

class PersistentTicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# --- BOT CORE ---
class EchoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(PersistentTicketLauncher())
        self.add_view(VerificationView())
        self.add_view(CloseTicketView())
        await self.tree.sync()

bot = EchoBot()

@tasks.loop(minutes=5)
async def update_stats():
    await bot.wait_until_ready()
    guild = bot.get_guild(ID_SERWERA)
    if not guild: return
    now = datetime.datetime.now()
    stats = {
        ID_KANAL_GRACZE: f"👥 Gracze: {len([m for m in guild.members if not m.bot])}",
        ID_KANAL_BOTY: f"🤖 Boty: {len([m for m in guild.members if m.bot])}",
        ID_KANAL_DATA: f"📅 Data: {now.strftime('%d.%m.%Y')}",
        ID_KANAL_GODZINA: f"⏰ Godzina: {now.strftime('%H:%M')}"
    }
    for cid, name in stats.items():
        channel = guild.get_channel(cid)
        if channel:
            try: await channel.edit(name=name)
            except: pass

@bot.event
async def on_ready():
    print(f'>>> {bot.user} ONLINE <<<')
    if not update_stats.is_running(): update_stats.start()

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(ID_KANALU_POWITAN)
    if channel:
        embed = discord.Embed(title="Witaj na Echo RP!", description=f"Siemano {member.mention}! 🌴", color=discord.Color.green())
        embed.set_image(url=LINK_POWITANIE)
        await channel.send(embed=embed)
    role = member.guild.get_role(ID_ROLI_NIEZWERYFIKOWANY)
    if role: await member.add_roles(role)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(ID_KANALU_POWITAN)
    if channel:
        embed = discord.Embed(title="Obywatel wyjechał...", description=f"Żegnaj **{member.name}**! 😢", color=discord.Color.red())
        embed.set_image(url=LINK_POZEGNANIE)
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot: return
    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            try:
                chat = client_ai.chat.completions.create(
                    messages=[{"role": "system", "content": AI_PROMPT}, {"role": "user", "content": message.content}],
                    model="llama-3.1-8b-instant"
                )
                await message.reply(chat.choices[0].message.content)
            except: await message.reply("Błąd AI.")
    await bot.process_commands(message)

# --- KOMENDY ---

@bot.tree.command(name="setup-verification", description="Wysyła panel weryfikacji (Admin Only)")
@app_commands.default_permissions(administrator=True) # <--- Poprawny sposób ukrywania
async def s_v(itn):
    embed = discord.Embed(title="🛡️ Weryfikacja Echo RP", description="Kliknij przycisk poniżej.", color=discord.Color.green())
    embed.set_image(url=LINK_WERYFIKACJA)
    await itn.channel.send(embed=embed, view=VerificationView())
    await itn.response.send_message("Wysłano.", ephemeral=True)

@bot.tree.command(name="ticket-setup", description="Wysyła panel ticketów (Admin Only)")
@app_commands.default_permissions(administrator=True) # <--- Poprawny sposób ukrywania
async def t_s(itn):
    embed = discord.Embed(title="CENTRUM POMOCY", description="Wybierz kategorię z listy.", color=discord.Color.blue())
    embed.set_image(url=LINK_TICKETY_GLOWNY)
    await itn.channel.send(embed=embed, view=PersistentTicketLauncher())
    await itn.response.send_message("Wysłano.", ephemeral=True)

@bot.tree.command(name="propozycja", description="Wyślij propozycję zmian na serwerze")
async def propozycja(itn, tresc: str):
    chan = bot.get_channel(ID_KANALU_PROPOZYCJI)
    embed = discord.Embed(title="💡 PROPOZYCJA", description=tresc, color=discord.Color.gold())
    embed.set_author(name=itn.user.name, icon_url=itn.user.display_avatar.url)
    msg = await chan.send(embed=embed)
    await msg.add_reaction("✅"); await msg.add_reaction("❌")
    await itn.response.send_message("✅ Twoja propozycja została wysłana!", ephemeral=True)

@bot.tree.command(name="chat-clear-all", description="CZYŚCI WSZYSTKIE KANAŁY (Admin Only)")
@app_commands.default_permissions(administrator=True) # <--- Poprawny sposób ukrywania
async def clear_all(itn: discord.Interaction):
    await itn.response.send_message("🚀 Czyszczenie serwera rozpoczęte...", ephemeral=True)
    for channel in itn.guild.text_channels:
        try: await channel.purge(limit=None)
        except: pass
    await itn.followup.send("✅ Serwer wyczyszczony!", ephemeral=True)

bot.run(TOKEN)