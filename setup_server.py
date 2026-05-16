import discord
from discord import app_commands
import asyncio
import sys

import os
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
GUILD_ID = 1505118392623955990

# MACIRL Brand Colors
BRAND_BLUE = 0x00AAFF
BRAND_DARK = 0x1a1a2e
BRAND_GREEN = 0x00E676
BRAND_RED = 0xFF3D3D
BRAND_GOLD = 0xFFD700

intents = discord.Intents.all()
client = discord.Client(intents=intents)

async def clear_existing_channels(guild):
    for ch in guild.channels:
        try:
            await ch.delete()
        except:
            pass

async def setup_roles(guild):
    roles = {}
    # Clean up existing custom roles (keep @everyone and bot roles)
    for role in guild.roles:
        if role.name not in ['@everyone'] and not role.managed and role != guild.default_role:
            try:
                await role.delete()
            except:
                pass

    roles['owner'] = await guild.create_role(
        name="Owner", color=discord.Color(BRAND_GOLD),
        permissions=discord.Permissions.all(), hoist=True
    )
    roles['admin'] = await guild.create_role(
        name="Admin", color=discord.Color(0xFF4444),
        permissions=discord.Permissions(administrator=True), hoist=True
    )
    roles['moderator'] = await guild.create_role(
        name="Moderator", color=discord.Color(BRAND_BLUE),
        permissions=discord.Permissions(
            manage_messages=True, kick_members=True, ban_members=True,
            manage_channels=True, view_channel=True, send_messages=True,
            manage_roles=True, mute_members=True, move_members=True
        ), hoist=True
    )
    roles['vip'] = await guild.create_role(
        name="VIP Customer", color=discord.Color(BRAND_GOLD), hoist=True
    )
    roles['customer'] = await guild.create_role(
        name="Customer", color=discord.Color(BRAND_GREEN), hoist=True
    )
    roles['member'] = await guild.create_role(
        name="Member", color=discord.Color(0x7289DA), hoist=True
    )
    roles['unverified'] = await guild.create_role(
        name="Unverified", color=discord.Color(0x808080)
    )
    return roles

async def setup_channels(guild, roles):
    everyone = guild.default_role
    # Default: hide everything from unverified
    await everyone.edit(permissions=discord.Permissions(view_channel=False, send_messages=False))

    # ===== CATEGORY: INFORMATION =====
    info_cat = await guild.create_category("INFORMATION")
    await info_cat.set_permissions(everyone, view_channel=True, send_messages=False)
    await info_cat.set_permissions(roles['unverified'], view_channel=True, send_messages=False)

    # Welcome / Rules
    welcome_ch = await guild.create_text_channel("welcome-rules", category=info_cat)
    await welcome_ch.set_permissions(everyone, view_channel=True, send_messages=False)
    await welcome_ch.set_permissions(roles['unverified'], view_channel=True, send_messages=False)

    welcome_embed = discord.Embed(
        title="Welcome to MACIRL",
        description=(
            "Your one-stop shop for premium IPTV and Media Server services.\n\n"
            "**Please read the rules below and react with the checkmark to get verified.**"
        ),
        color=BRAND_BLUE
    )
    welcome_embed.add_field(name="Rule 1", value="Be respectful to all members and staff.", inline=False)
    welcome_embed.add_field(name="Rule 2", value="No spamming or advertising in any channel.", inline=False)
    welcome_embed.add_field(name="Rule 3", value="Do not share your login credentials with anyone.", inline=False)
    welcome_embed.add_field(name="Rule 4", value="Use the ticket system for support - don't DM staff.", inline=False)
    welcome_embed.add_field(name="Rule 5", value="No refunds after 24 hours of purchase.", inline=False)
    welcome_embed.add_field(name="Rule 6", value="Follow Discord's Terms of Service at all times.", inline=False)
    welcome_embed.set_footer(text="MACIRL | React below to verify and access the server")
    msg = await welcome_ch.send(embed=welcome_embed)
    await msg.add_reaction("✅")

    # Announcements
    announce_ch = await guild.create_text_channel("announcements", category=info_cat)
    await announce_ch.set_permissions(everyone, view_channel=True, send_messages=False)
    await announce_ch.set_permissions(roles['admin'], send_messages=True)
    await announce_ch.set_permissions(roles['owner'], send_messages=True)
    ann_embed = discord.Embed(
        title="Announcements",
        description="Stay tuned for the latest updates, new plans, maintenance notices, and special offers from MACIRL.",
        color=BRAND_BLUE
    )
    await announce_ch.send(embed=ann_embed)

    # FAQ
    faq_ch = await guild.create_text_channel("faq", category=info_cat)
    await faq_ch.set_permissions(everyone, view_channel=True, send_messages=False)

    faq_embed = discord.Embed(title="Frequently Asked Questions", color=BRAND_BLUE)
    faq_embed.add_field(name="What is IPTV?", value="IPTV (Internet Protocol Television) lets you stream live TV channels and on-demand content over the internet. No dish or antenna needed.", inline=False)
    faq_embed.add_field(name="What devices are supported?", value="Android, iOS, Firestick, Smart TVs (Samsung/LG), Windows, Mac, and more. Check the wiki for setup guides.", inline=False)
    faq_embed.add_field(name="How do I order?", value="Head to the order-here channel and follow the instructions, or open a support ticket.", inline=False)
    faq_embed.add_field(name="How fast do I get my login?", value="Most orders are set up within 1-2 hours. During busy times it may take up to 12 hours.", inline=False)
    faq_embed.add_field(name="Do you offer trials?", value="Yes! Ask in the order channel or open a ticket to request a 24-hour trial.", inline=False)
    faq_embed.add_field(name="What payment methods do you accept?", value="PayPal, bank transfer, and crypto. Details provided when ordering.", inline=False)
    faq_embed.add_field(name="What if my service goes down?", value="Open a support ticket and we'll sort it out ASAP. We aim to respond within a few hours.", inline=False)
    await faq_ch.send(embed=faq_embed)

    # ===== CATEGORY: SHOP =====
    shop_cat = await guild.create_category("SHOP")
    await shop_cat.set_permissions(everyone, view_channel=False)
    await shop_cat.set_permissions(roles['member'], view_channel=True, send_messages=False)
    await shop_cat.set_permissions(roles['customer'], view_channel=True, send_messages=False)
    await shop_cat.set_permissions(roles['vip'], view_channel=True, send_messages=False)

    # IPTV Plans
    iptv_ch = await guild.create_text_channel("iptv-plans", category=shop_cat)
    await iptv_ch.set_permissions(roles['member'], view_channel=True, send_messages=False)
    iptv_embed = discord.Embed(
        title="IPTV Plans & Pricing",
        description="Premium IPTV with 20,000+ live channels, sports, movies, and TV shows.",
        color=BRAND_GREEN
    )
    iptv_embed.add_field(name="1 Month", value="$XX AUD\n1 Connection", inline=True)
    iptv_embed.add_field(name="3 Months", value="$XX AUD\n1 Connection", inline=True)
    iptv_embed.add_field(name="6 Months", value="$XX AUD\n1 Connection", inline=True)
    iptv_embed.add_field(name="12 Months", value="$XX AUD\n1 Connection", inline=True)
    iptv_embed.add_field(name="Multi-Connection", value="Add extra connections at a discounted rate. Ask for pricing.", inline=False)
    iptv_embed.add_field(name="Features", value="- Live TV (20,000+ channels)\n- EPG (TV Guide)\n- Catch-up / Timeshift\n- VOD (Movies & Series)\n- Sports (PPV included)\n- HD / FHD / 4K quality", inline=False)
    iptv_embed.set_footer(text="MACIRL | Prices are placeholders - update with your actual pricing")
    await iptv_ch.send(embed=iptv_embed)

    # Media Server Plans
    media_ch = await guild.create_text_channel("media-server-plans", category=shop_cat)
    await media_ch.set_permissions(roles['member'], view_channel=True, send_messages=False)
    media_embed = discord.Embed(
        title="Media Server Plans & Pricing",
        description="Personal media server access with massive libraries of movies and TV shows.",
        color=BRAND_GREEN
    )
    media_embed.add_field(name="1 Month", value="$XX AUD", inline=True)
    media_embed.add_field(name="3 Months", value="$XX AUD", inline=True)
    media_embed.add_field(name="6 Months", value="$XX AUD", inline=True)
    media_embed.add_field(name="12 Months", value="$XX AUD", inline=True)
    media_embed.add_field(name="Features", value="- Thousands of Movies (updated daily)\n- Full TV Series library\n- 4K / HDR content\n- Request system for new content\n- Works on all devices\n- Multiple profiles", inline=False)
    media_embed.set_footer(text="MACIRL | Prices are placeholders - update with your actual pricing")
    await media_ch.send(embed=media_embed)

    # Order Here
    order_ch = await guild.create_text_channel("order-here", category=shop_cat)
    await order_ch.set_permissions(roles['member'], view_channel=True, send_messages=True)
    order_embed = discord.Embed(
        title="How to Order",
        description=(
            "**To place an order, open a support ticket using the button in the support-tickets channel.**\n\n"
            "Include the following in your ticket:\n"
            "1. What service you want (IPTV / Media Server / Both)\n"
            "2. Which plan (duration)\n"
            "3. Number of connections needed\n"
            "4. Preferred payment method\n\n"
            "We'll get back to you ASAP with payment details and setup instructions."
        ),
        color=BRAND_GOLD
    )
    order_embed.set_footer(text="MACIRL | Fast setup, friendly service")
    await order_ch.send(embed=order_embed)

    # ===== CATEGORY: WIKI / SETUP GUIDES =====
    wiki_cat = await guild.create_category("WIKI & SETUP GUIDES")
    await wiki_cat.set_permissions(everyone, view_channel=False)
    await wiki_cat.set_permissions(roles['member'], view_channel=True, send_messages=False)
    await wiki_cat.set_permissions(roles['customer'], view_channel=True, send_messages=False)

    # IPTV Setup Guides
    iptv_wiki = await guild.create_text_channel("iptv-setup-guides", category=wiki_cat)
    await iptv_wiki.set_permissions(roles['member'], view_channel=True, send_messages=False)

    # Android
    android_embed = discord.Embed(title="IPTV Setup - Android (Phone/Tablet/TV Box)", color=BRAND_BLUE)
    android_embed.add_field(name="Recommended App: TiviMate", value=(
        "1. Download TiviMate from the Google Play Store\n"
        "2. Open the app and select 'Add Playlist'\n"
        "3. Choose 'Xtream Codes' as the playlist type\n"
        "4. Enter your server URL, username, and password (provided after purchase)\n"
        "5. Click 'Next' and wait for channels to load\n"
        "6. Enjoy!"
    ), inline=False)
    android_embed.add_field(name="Alternative App: IPTV Smarters Pro", value=(
        "1. Download IPTV Smarters Pro from the Play Store\n"
        "2. Select 'Login with Xtream Codes API'\n"
        "3. Enter your server URL, username, and password\n"
        "4. Click 'Add User' and wait for it to load\n"
        "5. Select Live TV, Movies, or Series"
    ), inline=False)
    await iptv_wiki.send(embed=android_embed)

    # Firestick
    fire_embed = discord.Embed(title="IPTV Setup - Amazon Firestick", color=BRAND_BLUE)
    fire_embed.add_field(name="Step 1: Enable Unknown Sources", value=(
        "Settings > My Fire TV > Developer Options > Install Unknown Apps > Turn ON for Silk Browser"
    ), inline=False)
    fire_embed.add_field(name="Step 2: Install Downloader App", value=(
        "Go to the Amazon App Store and search for 'Downloader'. Install it."
    ), inline=False)
    fire_embed.add_field(name="Step 3: Install TiviMate", value=(
        "1. Open Downloader\n"
        "2. Enter the URL for TiviMate APK (ask in support ticket)\n"
        "3. Download and install\n"
        "4. Open TiviMate and follow the Android setup steps above"
    ), inline=False)
    await iptv_wiki.send(embed=fire_embed)

    # iOS
    ios_embed = discord.Embed(title="IPTV Setup - iPhone / iPad", color=BRAND_BLUE)
    ios_embed.add_field(name="Recommended App: IPTV Smarters", value=(
        "1. Download 'IPTV Smarters Player' from the App Store\n"
        "2. Select 'Xtream Codes API' login\n"
        "3. Enter your server URL, username, and password\n"
        "4. Tap 'Add User'\n"
        "5. Browse Live TV, VOD, and Series"
    ), inline=False)
    ios_embed.add_field(name="Alternative: GSE Smart IPTV", value=(
        "1. Download GSE Smart IPTV from the App Store\n"
        "2. Go to Remote Playlists > Add Xtream Codes API\n"
        "3. Enter your credentials\n"
        "4. Save and enjoy"
    ), inline=False)
    await iptv_wiki.send(embed=ios_embed)

    # Smart TV
    tv_embed = discord.Embed(title="IPTV Setup - Smart TV (Samsung / LG)", color=BRAND_BLUE)
    tv_embed.add_field(name="Samsung Smart TV", value=(
        "1. Open the Samsung App Store on your TV\n"
        "2. Search for 'Smart IPTV' or 'IPTV Smarters'\n"
        "3. Install and open the app\n"
        "4. Enter your Xtream Codes credentials\n"
        "5. If Smart IPTV: visit siptv.app/mylist on your phone to upload your M3U URL"
    ), inline=False)
    tv_embed.add_field(name="LG Smart TV", value=(
        "1. Open the LG Content Store\n"
        "2. Search for 'Smart IPTV'\n"
        "3. Install and open\n"
        "4. Note the MAC address shown on screen\n"
        "5. Visit siptv.app/mylist and enter your MAC + M3U URL\n"
        "6. Restart the app"
    ), inline=False)
    await iptv_wiki.send(embed=tv_embed)

    # Windows/Mac
    pc_embed = discord.Embed(title="IPTV Setup - Windows / Mac", color=BRAND_BLUE)
    pc_embed.add_field(name="Windows", value=(
        "1. Download VLC Media Player (free) from videolan.org\n"
        "2. Open VLC > Media > Open Network Stream\n"
        "3. Paste your M3U URL\n"
        "4. Click Play\n\n"
        "OR use IPTV Smarters for Windows (download from the official site)"
    ), inline=False)
    pc_embed.add_field(name="Mac", value=(
        "1. Download IINA player or VLC for Mac\n"
        "2. Open > Network Stream\n"
        "3. Paste your M3U URL\n"
        "4. Enjoy"
    ), inline=False)
    await iptv_wiki.send(embed=pc_embed)

    # Media Server Setup Guides
    media_wiki = await guild.create_text_channel("media-server-setup", category=wiki_cat)
    await media_wiki.set_permissions(roles['member'], view_channel=True, send_messages=False)

    plex_embed = discord.Embed(title="Media Server Setup - All Devices", color=BRAND_BLUE)
    plex_embed.add_field(name="Step 1: Get the App", value=(
        "Download the Plex or Emby app on your device:\n"
        "- Android: Google Play Store\n"
        "- iOS: App Store\n"
        "- Firestick: Amazon App Store\n"
        "- Smart TV: Your TV's app store\n"
        "- Windows/Mac: plex.tv/downloads or emby.media/download"
    ), inline=False)
    plex_embed.add_field(name="Step 2: Accept Invite", value=(
        "After purchase, you'll receive an email invite to the media server.\n"
        "Click the link in the email to accept access.\n"
        "If you don't see it, check your spam folder."
    ), inline=False)
    plex_embed.add_field(name="Step 3: Sign In", value=(
        "Open the app and sign in with the account you used to accept the invite.\n"
        "The shared library will appear automatically."
    ), inline=False)
    plex_embed.add_field(name="Step 4: Request Content", value=(
        "Want a specific movie or show? Use the request channel or open a support ticket.\n"
        "Most requests are fulfilled within 24 hours."
    ), inline=False)
    await media_wiki.send(embed=plex_embed)

    # Troubleshooting
    trouble_ch = await guild.create_text_channel("troubleshooting", category=wiki_cat)
    await trouble_ch.set_permissions(roles['member'], view_channel=True, send_messages=False)

    trouble_embed = discord.Embed(title="Troubleshooting Guide", color=BRAND_RED)
    trouble_embed.add_field(name="IPTV buffering or freezing?", value=(
        "- Check your internet speed (minimum 25mbps recommended)\n"
        "- Try switching from WiFi to ethernet/wired connection\n"
        "- Clear the app cache and restart\n"
        "- Try a different player app\n"
        "- Use a VPN if your ISP is throttling"
    ), inline=False)
    trouble_embed.add_field(name="Cannot connect / login failed?", value=(
        "- Double-check your username and password (case sensitive)\n"
        "- Make sure the server URL is correct\n"
        "- Check if your subscription has expired\n"
        "- Open a support ticket if the issue persists"
    ), inline=False)
    trouble_embed.add_field(name="Media server not showing content?", value=(
        "- Make sure you accepted the invite email\n"
        "- Sign out and back in on the app\n"
        "- Check for app updates\n"
        "- Open a support ticket"
    ), inline=False)
    trouble_embed.add_field(name="App crashing?", value=(
        "- Update the app to the latest version\n"
        "- Clear app data/cache\n"
        "- Uninstall and reinstall\n"
        "- Try an alternative app from the setup guides"
    ), inline=False)
    await trouble_ch.send(embed=trouble_embed)

    # ===== CATEGORY: COMMUNITY =====
    comm_cat = await guild.create_category("COMMUNITY")
    await comm_cat.set_permissions(everyone, view_channel=False)
    await comm_cat.set_permissions(roles['member'], view_channel=True, send_messages=True)

    gen_ch = await guild.create_text_channel("general-chat", category=comm_cat)
    reviews_ch = await guild.create_text_channel("reviews-testimonials", category=comm_cat)
    await reviews_ch.set_permissions(roles['member'], view_channel=True, send_messages=True)

    review_embed = discord.Embed(
        title="Customer Reviews",
        description="Happy with the service? Drop a review here! Your feedback helps us grow and helps new customers feel confident.",
        color=BRAND_GOLD
    )
    review_embed.set_footer(text="MACIRL | We appreciate every review")
    await reviews_ch.send(embed=review_embed)

    # ===== CATEGORY: SUPPORT =====
    support_cat = await guild.create_category("SUPPORT")
    await support_cat.set_permissions(everyone, view_channel=False)
    await support_cat.set_permissions(roles['member'], view_channel=True, send_messages=False)

    ticket_ch = await guild.create_text_channel("support-tickets", category=support_cat)
    await ticket_ch.set_permissions(roles['member'], view_channel=True, send_messages=False)

    ticket_embed = discord.Embed(
        title="Need Help? Open a Support Ticket",
        description=(
            "Click the button below to open a private support ticket.\n\n"
            "Use tickets for:\n"
            "- Placing orders\n"
            "- Technical support\n"
            "- Account issues\n"
            "- General questions\n\n"
            "**React with the ticket emoji below to open a ticket.**"
        ),
        color=BRAND_BLUE
    )
    ticket_embed.set_footer(text="MACIRL Support | We aim to respond within a few hours")
    ticket_msg = await ticket_ch.send(embed=ticket_embed)
    await ticket_msg.add_reaction("\U0001F3AB")

    # ===== CATEGORY: ADMIN (hidden) =====
    admin_cat = await guild.create_category("ADMIN")
    await admin_cat.set_permissions(everyone, view_channel=False)
    await admin_cat.set_permissions(roles['admin'], view_channel=True, send_messages=True)
    await admin_cat.set_permissions(roles['owner'], view_channel=True, send_messages=True)

    admin_ch = await guild.create_text_channel("admin-chat", category=admin_cat)
    logs_ch = await guild.create_text_channel("bot-logs", category=admin_cat)

    return {
        'welcome': welcome_ch, 'announce': announce_ch, 'ticket': ticket_ch,
        'general': gen_ch, 'logs': logs_ch, 'ticket_msg_id': ticket_msg.id,
        'welcome_msg_id': msg.id
    }

@client.event
async def on_ready():
    print(f"Bot logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"ERROR: Cannot find guild {GUILD_ID}. Make sure the bot is invited to the server.")
        await client.close()
        return

    print("Setting up MACIRL server...")

    print("  Creating roles...")
    roles = await setup_roles(guild)

    print("  Clearing existing channels...")
    await clear_existing_channels(guild)

    print("  Creating channels and embeds...")
    channels = await setup_channels(guild, roles)

    # Save config for the persistent bot
    config = {
        'guild_id': GUILD_ID,
        'welcome_msg_id': channels['welcome_msg_id'],
        'ticket_msg_id': channels['ticket_msg_id'],
        'welcome_channel_id': channels['welcome'].id,
        'ticket_channel_id': channels['ticket'].id,
        'logs_channel_id': channels['logs'].id,
        'general_channel_id': channels['general'].id,
        'member_role_id': roles['member'].id,
        'unverified_role_id': roles['unverified'].id,
        'customer_role_id': roles['customer'].id,
    }

    with open('/var/lib/freelancer/projects/40346083/discord-bot/config.py', 'w') as f:
        f.write("# Auto-generated server config\n")
        for k, v in config.items():
            f.write(f"{k.upper()} = {v}\n")

    print("\n  Server setup complete!")
    print(f"  Roles created: {', '.join(roles.keys())}")
    print(f"  Config saved to config.py")
    print("\n  Now run the persistent bot: python3 bot.py")

    await client.close()

client.run(BOT_TOKEN)
