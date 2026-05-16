import discord
from discord.ext import commands
import asyncio
import datetime
from config import *

import os
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

BRAND_BLUE = 0x00AAFF
BRAND_GREEN = 0x00E676
BRAND_RED = 0xFF3D3D
BRAND_GOLD = 0xFFD700

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

ticket_count = 0

@bot.event
async def on_ready():
    print(f"MACIRL Bot online as {bot.user}")
    logs = bot.get_channel(LOGS_CHANNEL_ID)
    if logs:
        embed = discord.Embed(
            title="Bot Online",
            description=f"MACIRL Bot started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            color=BRAND_GREEN
        )
        await logs.send(embed=embed)

# ===== VERIFICATION SYSTEM =====
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    member = guild.get_member(payload.user_id)
    if not member:
        return

    # Verification reaction on welcome message
    if payload.message_id == WELCOME_MSG_ID and str(payload.emoji) == "✅":
        member_role = guild.get_role(MEMBER_ROLE_ID)
        unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)
        if member_role:
            await member.add_roles(member_role)
        if unverified_role and unverified_role in member.roles:
            await member.remove_roles(unverified_role)

        # Welcome in general
        general = bot.get_channel(GENERAL_CHANNEL_ID)
        if general:
            embed = discord.Embed(
                description=f"Welcome to MACIRL, {member.mention}! Check out our plans and feel free to ask any questions.",
                color=BRAND_BLUE
            )
            await general.send(embed=embed)

        # Log
        logs = bot.get_channel(LOGS_CHANNEL_ID)
        if logs:
            await logs.send(f"[VERIFY] {member} verified and given Member role.")

    # Ticket creation
    if payload.message_id == TICKET_MSG_ID and str(payload.emoji) == "\U0001F3AB":
        # Remove the reaction
        channel = bot.get_channel(payload.channel_id)
        if channel:
            try:
                msg = await channel.fetch_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, member)
            except:
                pass

        # Check if they already have a ticket open
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower().replace(' ', '-')[:20]}")
        if existing:
            await channel.send(f"{member.mention} You already have an open ticket: {existing.mention}", delete_after=10)
            return

        # Create ticket channel
        global ticket_count
        ticket_count += 1
        ticket_name = f"ticket-{member.name.lower().replace(' ', '-')[:20]}"

        # Find or create a tickets category
        tickets_cat = discord.utils.get(guild.categories, name="OPEN TICKETS")
        if not tickets_cat:
            tickets_cat = await guild.create_category("OPEN TICKETS")
            await tickets_cat.set_permissions(guild.default_role, view_channel=False)

        # Create the ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        # Add admin/mod access
        for role_name in ['Admin', 'Owner', 'Moderator']:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ticket_ch = await guild.create_text_channel(ticket_name, category=tickets_cat, overwrites=overwrites)

        embed = discord.Embed(
            title="Support Ticket",
            description=(
                f"Hey {member.mention}, thanks for opening a ticket!\n\n"
                "Please describe what you need help with:\n"
                "- **Order**: What service + plan you want\n"
                "- **Support**: Describe your issue\n"
                "- **Question**: Ask away\n\n"
                "A team member will be with you shortly.\n"
                "Type `!close` to close this ticket when done."
            ),
            color=BRAND_BLUE
        )
        embed.set_footer(text="MACIRL Support")
        await ticket_ch.send(embed=embed)

        # Notify in support channel
        await channel.send(f"{member.mention} Ticket created: {ticket_ch.mention}", delete_after=10)

        # Log
        logs = bot.get_channel(LOGS_CHANNEL_ID)
        if logs:
            await logs.send(f"[TICKET] {member} opened ticket: {ticket_ch.mention}")

# ===== TICKET CLOSE COMMAND =====
@bot.command()
async def close(ctx):
    if not ctx.channel.name.startswith("ticket-"):
        return

    embed = discord.Embed(
        title="Ticket Closed",
        description=f"Ticket closed by {ctx.author.mention}. This channel will be deleted in 10 seconds.",
        color=BRAND_RED
    )
    await ctx.send(embed=embed)

    # Log
    logs = bot.get_channel(LOGS_CHANNEL_ID)
    if logs:
        await logs.send(f"[TICKET] {ctx.channel.name} closed by {ctx.author}")

    await asyncio.sleep(10)
    await ctx.channel.delete()

# ===== WELCOME NEW MEMBERS =====
@bot.event
async def on_member_join(member):
    # Give unverified role
    unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
    if unverified_role:
        await member.add_roles(unverified_role)

    # DM the user
    try:
        embed = discord.Embed(
            title="Welcome to MACIRL!",
            description=(
                "Thanks for joining! To access the server, please head to the "
                "**#welcome-rules** channel and react with ✅ to verify.\n\n"
                "Once verified, you'll be able to see all channels including our "
                "plans, setup guides, and support."
            ),
            color=BRAND_BLUE
        )
        await member.send(embed=embed)
    except:
        pass

    # Log
    logs = bot.get_channel(LOGS_CHANNEL_ID)
    if logs:
        await logs.send(f"[JOIN] {member} joined the server. Given Unverified role.")

# ===== MEMBER LEAVE =====
@bot.event
async def on_member_remove(member):
    logs = bot.get_channel(LOGS_CHANNEL_ID)
    if logs:
        await logs.send(f"[LEAVE] {member} left the server.")

# ===== MODERATION COMMANDS =====
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    embed = discord.Embed(description=f"{member} has been kicked. Reason: {reason}", color=BRAND_RED)
    await ctx.send(embed=embed)
    logs = bot.get_channel(LOGS_CHANNEL_ID)
    if logs:
        await logs.send(f"[MOD] {member} kicked by {ctx.author}. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    embed = discord.Embed(description=f"{member} has been banned. Reason: {reason}", color=BRAND_RED)
    await ctx.send(embed=embed)
    logs = bot.get_channel(LOGS_CHANNEL_ID)
    if logs:
        await logs.send(f"[MOD] {member} banned by {ctx.author}. Reason: {reason}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 10):
    if amount > 100:
        amount = 100
    deleted = await ctx.channel.purge(limit=amount + 1)
    embed = discord.Embed(description=f"Deleted {len(deleted) - 1} messages.", color=BRAND_BLUE)
    await ctx.send(embed=embed, delete_after=5)

# ===== ANTI-SPAM =====
spam_tracker = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return

    # Simple anti-spam: 5 messages in 5 seconds = timeout
    uid = message.author.id
    now = datetime.datetime.now()
    if uid not in spam_tracker:
        spam_tracker[uid] = []
    spam_tracker[uid].append(now)
    spam_tracker[uid] = [t for t in spam_tracker[uid] if (now - t).total_seconds() < 5]

    if len(spam_tracker[uid]) >= 5:
        try:
            await message.author.timeout(datetime.timedelta(minutes=5), reason="Spam detected")
            await message.channel.send(f"{message.author.mention} has been timed out for 5 minutes (spam detected).", delete_after=10)
            logs = bot.get_channel(LOGS_CHANNEL_ID)
            if logs:
                await logs.send(f"[SPAM] {message.author} timed out for spam in {message.channel.mention}")
        except:
            pass
        spam_tracker[uid] = []

    await bot.process_commands(message)

# ===== INFO COMMAND =====
@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title="MACIRL Bot Commands",
        color=BRAND_BLUE
    )
    embed.add_field(name="!info", value="Show this help message", inline=False)
    embed.add_field(name="!close", value="Close a support ticket (use inside a ticket channel)", inline=False)
    embed.add_field(name="!kick @user [reason]", value="Kick a member (Mod+)", inline=False)
    embed.add_field(name="!ban @user [reason]", value="Ban a member (Admin+)", inline=False)
    embed.add_field(name="!purge [number]", value="Delete messages in channel (Mod+)", inline=False)
    embed.set_footer(text="MACIRL Bot")
    await ctx.send(embed=embed)

print("Starting MACIRL Bot...")
bot.run(BOT_TOKEN)
