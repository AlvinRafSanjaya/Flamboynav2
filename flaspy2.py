import discord
from discord.ext import commands, menus, tasks
from discord.ext.commands import Bot
from discord.ext.commands import has_permissions
import asyncio
import random
import time
import io
import requests
import os
import sqlite3

# Inisialisasi koneksi database SQLite
conn = sqlite3.connect('role_auto.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS role_auto (
              id INTEGER PRIMARY KEY,
              server_id INTEGER,
              role_id INTEGER,
              role_name TEXT)''')

# Menyalin data dari tabel lama ke tabel baru
cursor.execute('INSERT INTO role_auto (server_id, role_id) SELECT NULL, role_id FROM role_auto')

# Komit perubahan ke database
conn.commit()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.typing = False
intents.presences = False
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!', intents=intents)

# Daftar untuk menyimpan ID role otomatis
role_auto_list = []

#Fitur pertama

@bot.event
async def on_ready():
    print(f'Bot telah masuk sebagai {bot.user.name}')
    
    # Mengubah status bot
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'Server {len(bot.guilds)}'))
    
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Menghindari merespons pesan dari diri sendiri
    if message.content.lower() == 'halo':
        await message.channel.send('Halo! Selamat datang di server kami. Jika ingin mengetahui fiturnya silakan ketik !list ya nekooo')
    
    await bot.process_commands(message)  # Memproses perintah lainnya (jika ada) setelah mengecek pesan

# Hapus perintah !halo yang lama
bot.remove_command('halo')
        
#fitur Kedua

@bot.command()
async def clear(ctx):
    # Memeriksa jika penulis pesan adalah administrator atau memiliki izin "Manage Messages"
    if ctx.author.guild_permissions.manage_messages:
        # Membuat pesan konfirmasi dengan embed warna yang disebutkan
        confirmation_embed = discord.Embed(
            title=f'Konfirmasi Penghapusan Pesan',
            description=f'Apakah Anda yakin ingin menghapus semua pesan di channel ini?',
            color=int('2f3136', 16)  # Menggunakan warna #2f3136
        )

        confirmation_msg = await ctx.send(embed=confirmation_embed)

        # Menambahkan emoji ceklis dan silang ke pesan konfirmasi
        await confirmation_msg.add_reaction('✅')
        await confirmation_msg.add_reaction('❌')

        def check(reaction, user):
            return user == ctx.author and reaction.message == confirmation_msg and str(reaction.emoji) in ['✅', '❌']

        try:
            reaction, _ = await bot.wait_for('reaction_add', check=check, timeout=30)  # Menunggu respons dari pengguna
        except TimeoutError:
            await ctx.send('Waktu habis. Pembatalan perintah.')
        else:
            if str(reaction.emoji) == '✅':
                await ctx.channel.purge()  # Menghapus semua pesan di channel
                await ctx.send('Semua pesan di channel ini telah dihapus!', delete_after=5)
            else:
                await ctx.send('Penghapusan pesan dibatalkan.')
    else:
        await ctx.send('Anda tidak memiliki izin untuk menggunakan perintah ini!')
        
#fitur ketiga

# Daftar untuk menyimpan prefix khusus server
custom_prefixes = {}

# Perintah untuk mengubah prefix
@bot.command()
async def setprefix(ctx, new_prefix: str):
    # Memeriksa apakah pengguna yang menjalankan perintah adalah administrator server
    if ctx.author.guild_permissions.administrator:
        # Simpan prefix baru ke dalam daftar prefix khusus server
        custom_prefixes[ctx.guild.id] = new_prefix
        
        # Buat pesan embed dengan tag warna #2f3136
        embed = discord.Embed(
            title='Prefix Bot Diubah',
            description=f'Prefix bot diubah menjadi: {new_prefix}',
            color=int('2f3136', 16)  # Menggunakan warna #2f3136
        )
        
        # Kirim pesan embed
        await ctx.send(embed=embed)
    else:
        await ctx.send('Anda tidak memiliki izin untuk mengubah prefix bot!')

# Mendefinisikan prefix yang disesuaikan
def get_custom_prefix(bot, message):
    # Mengambil prefix khusus server jika ada, jika tidak, gunakan prefix default '!'
    return custom_prefixes.get(message.guild.id, '!')

# Mengatur prefix khusus
bot.command_prefix = get_custom_prefix

#fitur keempat

@bot.command()
async def roleauto(ctx, role_id: int):
    if ctx.author.guild_permissions.administrator:
        role = discord.utils.get(ctx.guild.roles, id=role_id)

        if role is not None:
            # Memasukkan ID dan nama peran otomatis beserta ID server ke dalam database
            cursor.execute("INSERT INTO role_auto (server_id, role_id, role_name) VALUES (?, ?, ?)", (ctx.guild.id, role.id, role.name))
            conn.commit()

            # Membuat pesan embed untuk memberikan tanggapan
            embed = discord.Embed(
                title='Role Otomatis Ditambahkan',
                description=f'Role "{role.name}" ({role.id}) telah ditambahkan sebagai role otomatis di server ini.',
                color=int('2f3136', 16)  # Menggunakan warna #2f3136
            )

            await ctx.send(embed=embed)
        else:
            await ctx.send('Role dengan ID tersebut tidak ditemukan di server ini.')
    else:
        await ctx.send('Anda tidak memiliki izin untuk menggunakan perintah ini!')

@bot.event
async def on_member_join(member):
    server_id = member.guild.id
    for row in cursor.execute("SELECT role_id FROM role_auto WHERE server_id = ?", (server_id,)):
        role_id = row[0]
        role = discord.utils.get(member.guild.roles, id=role_id)
        if role:
            await member.add_roles(role)

        
#fitur terakhir 

@bot.command()
async def list(ctx):
    # Membuat pesan embed yang akan menampilkan daftar fitur Anda
    help_embed = discord.Embed(
        title='Daftar Fitur Bot',
        color=int('2f3136', 16)
    )

    # Menambahkan deskripsi untuk setiap fitur
    help_embed.add_field(name='!clear (1-1000)', value='Menghapus pesan', inline=False)
    help_embed.add_field(name='!setprefix [prefix]', value='Mengubah prefix bot', inline=False)
    help_embed.add_field(name='!roleauto (id role)', value='Menambah role otomatis', inline=False)
    
    # Menambahkan foto profil bot ke pesan embed (gantilah URL sesuai dengan URL gambar yang ingin Anda gunakan)
    help_embed.set_thumbnail(url=bot.user.avatar.url)

    # Mengirimkan pesan embed ke server
    await ctx.send(embed=help_embed)
    
# Jalankan bot dengan token Anda
bot.run('MTE1ODM3Mjk3NDI3NDAyNzU1Mg.G0v3wj.lc-hvb-cpm2gKNHsryawE5hfF4Xs3TfROh8FY4')
