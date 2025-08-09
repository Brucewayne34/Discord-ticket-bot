import discord
from discord.ext import commands, tasks
import json
import random
import os
import datetime
import asyncio
import re
import time
import aiohttp
import platform
import socket
import typing
from typing import Optional
try:
    import psutil
except ImportError:
    psutil = None
try:
    import requests
except ImportError:
    requests = None

# ===== MULTI-SERVER CONFIGURATION =====

def load_guild_config(guild_id):
    """Load configuration for a specific guild"""
    config_path = f"configs/{guild_id}.json"
    if not os.path.exists(config_path):
        return None

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def save_guild_config(guild_id, config_data):
    """Save configuration for a specific guild"""
    os.makedirs("configs", exist_ok=True)
    config_path = f"configs/{guild_id}.json"
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=4)

def load_guild_tickets(guild_id):
    """Load tickets for a specific guild"""
    ticket_path = f"tickets/{guild_id}.json"
    if not os.path.exists(ticket_path):
        return {}

    try:
        with open(ticket_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_guild_tickets(guild_id, tickets_data):
    """Save tickets for a specific guild"""
    os.makedirs("tickets", exist_ok=True)
    ticket_path = f"tickets/{guild_id}.json"
    with open(ticket_path, "w") as f:
        json.dump(tickets_data, f, indent=4)

def load_guild_blacklist(guild_id):
    """Load blacklisted users for a guild"""
    blacklist_path = f"blacklists/{guild_id}.json"
    if not os.path.exists(blacklist_path):
        return []

    try:
        with open(blacklist_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_guild_blacklist(guild_id, blacklist_data):
    """Save blacklisted users for a guild"""
    os.makedirs("blacklists", exist_ok=True)
    blacklist_path = f"blacklists/{guild_id}.json"
    with open(blacklist_path, "w") as f:
        json.dump(blacklist_data, f, indent=4)

def load_guild_warnings(guild_id):
    """Load warnings for a guild"""
    warnings_path = f"warnings/{guild_id}.json"
    if not os.path.exists(warnings_path):
        return {}

    try:
        with open(warnings_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_guild_warnings(guild_id, warnings_data):
    """Save warnings for a guild"""
    os.makedirs("warnings", exist_ok=True)
    warnings_path = f"warnings/{guild_id}.json"
    with open(warnings_path, "w") as f:
        json.dump(warnings_data, f, indent=4)

def load_guild_tags(guild_id):
    """Load custom tags for a guild"""
    tags_path = f"tags/{guild_id}.json"
    if not os.path.exists(tags_path):
        return {}

    try:
        with open(tags_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_guild_tags(guild_id, tags_data):
    """Save custom tags for a guild"""
    os.makedirs("tags", exist_ok=True)
    tags_path = f"tags/{guild_id}.json"
    with open(tags_path, "w") as f:
        json.dump(tags_data, f, indent=4)

def load_guild_panels(guild_id):
    """Load saved panels for a guild"""
    panels_path = f"panels/{guild_id}.json"
    if not os.path.exists(panels_path):
        return {}
    
    try:
        with open(panels_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_guild_panels(guild_id, panels_data):
    """Save panels for a guild"""
    os.makedirs("panels", exist_ok=True)
    panels_path = f"panels/{guild_id}.json"
    with open(panels_path, "w") as f:
        json.dump(panels_data, f, indent=4)

def get_guild_ticket_counter(guild_id):
    """Get the next ticket counter for a guild"""
    tickets = load_guild_tickets(guild_id)
    if not tickets:
        return 1
    return max([0] + [int(ticket_data.get("ticket_number", 0)) for ticket_data in tickets.values()]) + 1

def is_guild_configured(guild_id):
    """Check if a guild is configured"""
    return load_guild_config(guild_id) is not None

def get_embed_color(guild_id):
    """Get embed color for a guild"""
    config = load_guild_config(guild_id)
    if config and "embed_color" in config:
        return discord.Color.from_rgb(*config["embed_color"])
    return discord.Color.from_rgb(128, 0, 255)  # Default purple

def is_user_blacklisted(guild_id, user_id):
    """Check if user is blacklisted"""
    blacklist = load_guild_blacklist(guild_id)
    return user_id in blacklist

# ===== ANIMATED EMOJIS =====
ANIMATED_EMOJIS = {
    'ticket': '<a:Ticket:1401583771547074560>',
    'checkmark': '<a:checkmark:1401591542996664450>',
    'dart': '<a:dart:1401636272706949161>',
    'earth': '<a:earth:1401636310141112411>',
    'file': '<a:file:1401629622973759650>',
    'label': '<a:label:1401636213512736881>',
    'laptop': '<a:laptop:1401636098098073720>',
    'lightbulb': '<a:lightbulb:1401636070256410826>',
    'lock': '<a:lock:1401629561560502355>',
    'mobile': '<a:mobile:1401636122282426529>',
    'securepolice': '<a:securepolice:1401629481025667083>',
    'setting': '<a:setting:1401587347551948921>',
    'sparkle': '<a:sparkle:1401590956863651870>',
    'stats': '<a:stats:1401587832526602240>',
    'tickets': '<a:tickets:1401636154285101086>',
    'usermanage': '<a:usermanage:1401589445051941056>',
    'wave': '<a:wave:1401636185729794108>',
    'zap': '<a:zap:1401636244391329822>'
}

# Bot token - Get from environment variable for security
TOKEN = PASTE YOUR TOKEN HERE 
# Intents configuration
intents = discord.Intents.all()
intents.message_content = True

# Initialize bot with default prefix (can be overridden per guild)
bot = commands.Bot(command_prefix="-", intents=intents)
bot.remove_command('help')

# Rate limiting helper
class RateLimiter:
    def __init__(self, max_requests=3, time_window=2.0):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def wait_if_needed(self):
        now = time.time()
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

        if len(self.requests) >= self.max_requests:
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request)
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self.requests.append(now)

webhook_rate_limiter = RateLimiter(max_requests=3, time_window=2.0)

# ===== ENHANCED WEBHOOK MESSAGE RECREATION =====

async def recreate_messages_with_webhook(channel, messages_data):
    """Recreate messages using webhook to preserve avatars and names - FIXED VERSION"""
    webhook = None
    try:
        # Create a webhook for message recreation
        webhook = await channel.create_webhook(name="Ticket-Message-Recreation")
        
        # Track rate limiting
        processed = 0
        # Ensure messages_data is a list, not a coroutine
        if hasattr(messages_data, '__await__'):
            messages_data = await messages_data
        total_messages = len(messages_data)
        
        for i, msg_data in enumerate(messages_data):
            try:
                await webhook_rate_limiter.wait_if_needed()
                
                # Parse message data - Fixed parsing logic
                if not msg_data.strip() or ']: ' not in msg_data:
                    continue
                
                # Extract timestamp and content
                timestamp_end = msg_data.find('] ')
                if timestamp_end == -1:
                    continue
                    
                remaining = msg_data[timestamp_end + 2:]
                if ': ' not in remaining:
                    continue
                    
                user_info, content = remaining.split(': ', 1)
                
                # Parse user info: user_id|username|display_name
                user_parts = user_info.split('|')
                if len(user_parts) < 3:
                    continue
                
                user_id = user_parts[0]
                username = user_parts[1]
                display_name = user_parts[2]
                
                # Skip bot messages to avoid loops
                if user_id == str(bot.user.id):
                    continue
                
                # Try to get user avatar
                avatar_url = None
                try:
                    user = await bot.fetch_user(int(user_id))
                    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
                except:
                    pass
                
                # Clean content - remove any webhook mentions
                clean_content = content.strip()
                if not clean_content:
                    continue
                
                # Send message through webhook with error handling
                try:
                    await webhook.send(
                        content=clean_content[:2000],  # Discord message limit
                        username=display_name[:80],  # Discord username limit
                        avatar_url=avatar_url,
                        wait=False
                    )
                    processed += 1
                    
                    # Progress update every 10 messages
                    if processed % 10 == 0:
                        print(f"Recreated {processed}/{total_messages} messages...")
                        
                except discord.HTTPException as e:
                    print(f"Failed to send webhook message: {e}")
                    continue
                
                # Small delay to prevent overwhelming Discord
                await asyncio.sleep(0.7)
                
            except Exception as e:
                print(f"Error processing message {i}: {e}")
                continue
        
        print(f"Successfully recreated {processed}/{total_messages} messages")
        
    except discord.Forbidden:
        print("No permission to create webhook")
        # Fallback to regular messages
        await fallback_message_recreation(channel, messages_data[:10])
    except Exception as e:
        print(f"Error in webhook recreation: {e}")
        await fallback_message_recreation(channel, messages_data[:10])
    finally:
        # Always cleanup webhook
        if webhook:
            try:
                await webhook.delete()
            except:
                pass

async def fallback_message_recreation(channel, messages_data):
    """Fallback method for message recreation without webhooks"""
    try:
        for msg_data in messages_data:
            if not msg_data.strip():
                continue
                
            # Format as code block for fallback
            formatted_msg = f"```{msg_data[:1950]}```"
            await channel.send(formatted_msg)
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Fallback recreation failed: {e}")

# ===== TICKET PANEL & BUTTON VIEWS =====

class TicketPanelView(discord.ui.View):
    def __init__(self, button_names: list, guild_id: str):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        for name in button_names:
            self.add_item(ReasonButton(label=name, guild_id=guild_id))

class ReasonButton(discord.ui.Button):
    def __init__(self, label: str, guild_id: str):
        # Truncate label to 45 characters max to comply with Discord limits
        truncated_label = label[:45] if len(label) > 45 else label
        super().__init__(label=truncated_label, style=discord.ButtonStyle.primary, custom_id=f"reason_button_{guild_id}_{label}")
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        if not is_guild_configured(self.guild_id):
            await interaction.response.send_message(
                "❌ This server is not configured yet! An administrator needs to run `-setup` first.", 
                ephemeral=True
            )
            return

        # Check if user is blacklisted
        if is_user_blacklisted(self.guild_id, interaction.user.id):
            await interaction.response.send_message(
                "❌ You are blacklisted from creating tickets in this server.", 
                ephemeral=True
            )
            return

        # Check for existing open tickets
        tickets_data = load_guild_tickets(self.guild_id)
        user_open_tickets = [
            ticket for ticket in tickets_data.values() 
            if ticket["creator_id"] == interaction.user.id and not ticket.get("closed", False)
        ]
        
        config = load_guild_config(self.guild_id)
        max_tickets = config.get("max_tickets_per_user", 3)
        
        if len(user_open_tickets) >= max_tickets:
            await interaction.response.send_message(
                f"❌ You already have {len(user_open_tickets)} open tickets. Maximum allowed: {max_tickets}", 
                ephemeral=True
            )
            return

        await interaction.response.send_modal(ReasonModal(self.label, self.guild_id))

class ReasonModal(discord.ui.Modal, title='Reason for Ticket'):
    reason = discord.ui.TextInput(
        label='Describe your issue (max 500 characters)', 
        style=discord.TextStyle.paragraph, 
        max_length=500,
        placeholder="Describe your issue in detail..."
    )

    def __init__(self, button_name: str, guild_id: str):
        super().__init__()
        self.button_name = button_name
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        config = load_guild_config(self.guild_id)
        if not config:
            await interaction.response.send_message("❌ Server not configured!", ephemeral=True)
            return

        ticket_counter = get_guild_ticket_counter(self.guild_id)
        ticket_id = random.randint(10000, 99999)  # 5-digit ticket IDs

        tickets_data = load_guild_tickets(self.guild_id)
        while str(ticket_id) in tickets_data:
            ticket_id = random.randint(10000, 99999)

        ticket_channel_name = f"{self.button_name.lower()}-{ticket_counter}"
        guild = interaction.guild
        category = guild.get_channel(config["ticket_category_id"])

        if not category:
            await interaction.response.send_message("❌ Ticket category not found! Please check configuration.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True, 
                send_messages=True, 
                read_messages=True, 
                attach_files=True,
                add_reactions=True,
                embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, 
                send_messages=True, 
                read_messages=True, 
                attach_files=True,
                manage_channels=True,
                manage_webhooks=True
            )
        }

        for role_id in config["staff_role_ids"]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, 
                    send_messages=True, 
                    read_messages=True, 
                    attach_files=True,
                    manage_messages=True
                )

        try:
            ticket_channel = await guild.create_text_channel(
                ticket_channel_name, 
                category=category, 
                overwrites=overwrites,
                topic=f"Ticket #{ticket_id} | Created by {interaction.user} | Type: {self.button_name}"
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to create channels!", ephemeral=True)
            return

        tickets_data[str(ticket_id)] = {
            "channel_id": ticket_channel.id,
            "creator_id": interaction.user.id,
            "button_name": self.button_name,
            "ticket_number": ticket_counter,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "closed": False,
            "reopened": "No",
            "reason": self.reason.value,
            "added_users": [],
            "claimed_by": None,
            "priority": "medium",
            "notes": [],
            "tags": [],
            "status": "open"
        }
        save_guild_tickets(self.guild_id, tickets_data)

        embed_color = get_embed_color(self.guild_id)
        embed = discord.Embed(
            title=f"{ANIMATED_EMOJIS['ticket']} New Support Ticket",
            color=embed_color
        )
        embed.set_author(
            name=f"{interaction.user.display_name} ({interaction.user})", 
            icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
        )
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)
        
        embed.add_field(name=f"{ANIMATED_EMOJIS['usermanage']} Created by", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name=f"{ANIMATED_EMOJIS['label']} Type", value=f"`{self.button_name}`", inline=True)
        embed.add_field(name=f"{ANIMATED_EMOJIS['tickets']} Ticket ID", value=f"`{ticket_id}`", inline=True)
        embed.add_field(name=f"{ANIMATED_EMOJIS['file']} Reason", value=f"```{self.reason.value}```", inline=False)
        embed.add_field(name=f"{ANIMATED_EMOJIS['zap']} Priority", value="`Medium`", inline=True)
        embed.add_field(name=f"{ANIMATED_EMOJIS['stats']} Status", value="`Open`", inline=True)
        embed.set_footer(text=f"Ticket #{ticket_counter} • Created at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Get custom welcome message or use default
        welcome_msg = config.get("welcome_message", 
            f"**Welcome {interaction.user.mention}!** {ANIMATED_EMOJIS['wave']}\n\n"
            "Thank you for creating a ticket. Our support team will be with you shortly.\n"
            "Please provide any additional details about your issue while you wait."
        )

        view = TicketControlView(ticket_id, self.guild_id)
        await ticket_channel.send(welcome_msg, embed=embed, view=view)
        
        # Send confirmation
        await interaction.response.send_message(
            f"✅ Ticket created successfully! {ticket_channel.mention}", 
            ephemeral=True
        )

        # Log ticket creation
        log_channel = guild.get_channel(config["log_channel_id"])
        if log_channel:
            log_embed = discord.Embed(
                title=f"{ANIMATED_EMOJIS['ticket']} New Ticket Created",
                color=embed_color
            )
            log_embed.add_field(name="User", value=interaction.user.mention, inline=True)
            log_embed.add_field(name="Channel", value=ticket_channel.mention, inline=True)
            log_embed.add_field(name="ID", value=f"`{ticket_id}`", inline=True)
            log_embed.add_field(name="Type", value=f"`{self.button_name}`", inline=True)
            await log_channel.send(embed=log_embed)

# ===== ENHANCED TICKET CONTROL VIEWS =====

class TicketControlView(discord.ui.View):
    def __init__(self, ticket_id: int, guild_id: str):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        self.guild_id = guild_id
        self.add_item(CloseTicketButton(ticket_id, guild_id))
        self.add_item(ClaimTicketButton(ticket_id, guild_id))
        self.add_item(TranscriptButton(ticket_id, guild_id))
        self.add_item(RenameTicketButton(ticket_id, guild_id))

class CloseTicketButton(discord.ui.Button):
    def __init__(self, ticket_id: int, guild_id: str):
        super().__init__(
            label="Close Ticket",
            style=discord.ButtonStyle.danger,
            emoji=ANIMATED_EMOJIS['lock'],
            custom_id=f"close_ticket_{guild_id}_{ticket_id}"
        )
        self.ticket_id = ticket_id
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        config = load_guild_config(self.guild_id)
        if not config:
            await interaction.response.send_message("❌ Server not configured!", ephemeral=True)
            return

        tickets_data = load_guild_tickets(self.guild_id)
        ticket_data = tickets_data.get(str(self.ticket_id))

        if not ticket_data:
            await interaction.response.send_message("Ticket data not found.", ephemeral=True)
            return

        is_staff = any(role.id in config["staff_role_ids"] for role in interaction.user.roles)
        is_creator = interaction.user.id == ticket_data["creator_id"]
        is_claimer = ticket_data.get("claimed_by") == interaction.user.id

        if not (is_staff or is_creator or is_claimer):
            await interaction.response.send_message("❌ You do not have permission to close this ticket.", ephemeral=True)
            return

        view = ConfirmCloseView(self.ticket_id, self.guild_id)
        embed = discord.Embed(
            title="⚠️ Confirm Ticket Closure",
            description="Are you sure you want to close this ticket?\n\n**This action will:**\n• Archive all messages\n• Send logs to staff\n• Delete the channel after 10 seconds",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ClaimTicketButton(discord.ui.Button):
    def __init__(self, ticket_id: int, guild_id: str):
        super().__init__(
            label="Claim",
            style=discord.ButtonStyle.success,
            emoji=ANIMATED_EMOJIS['wave'],
            custom_id=f"claim_ticket_{guild_id}_{ticket_id}"
        )
        self.ticket_id = ticket_id
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        config = load_guild_config(self.guild_id)
        if not config:
            await interaction.response.send_message("❌ Server not configured!", ephemeral=True)
            return

        is_staff = any(role.id in config["staff_role_ids"] for role in interaction.user.roles)
        if not is_staff:
            await interaction.response.send_message("❌ Only staff members can claim tickets.", ephemeral=True)
            return

        tickets_data = load_guild_tickets(self.guild_id)
        ticket_data = tickets_data.get(str(self.ticket_id))

        if not ticket_data:
            await interaction.response.send_message("Ticket data not found.", ephemeral=True)
            return

        # Toggle claim/unclaim
        if ticket_data.get("claimed_by") == interaction.user.id:
            # Unclaim
            ticket_data["claimed_by"] = None
            ticket_data.pop("claimed_at", None)
            tickets_data[str(self.ticket_id)] = ticket_data
            save_guild_tickets(self.guild_id, tickets_data)

            embed_color = get_embed_color(self.guild_id)
            embed = discord.Embed(
                title="🔓 Ticket Unclaimed",
                description=f"This ticket has been unclaimed by {interaction.user.mention}",
                color=embed_color
            )
            await interaction.response.send_message(embed=embed)
            
            # Update button label
            self.label = "Claim"
            self.style = discord.ButtonStyle.success
            await interaction.edit_original_response(view=self.view)
            
        elif ticket_data.get("claimed_by"):
            claimer = interaction.guild.get_member(ticket_data["claimed_by"])
            claimer_name = claimer.display_name if claimer else "Unknown"
            await interaction.response.send_message(f"❌ This ticket is already claimed by {claimer_name}.", ephemeral=True)
            return
        else:
            # Claim
            ticket_data["claimed_by"] = interaction.user.id
            ticket_data["claimed_at"] = datetime.datetime.utcnow().isoformat()
            tickets_data[str(self.ticket_id)] = ticket_data
            save_guild_tickets(self.guild_id, tickets_data)

            embed_color = get_embed_color(self.guild_id)
            embed = discord.Embed(
                title="🎯 Ticket Claimed",
                description=f"This ticket has been claimed by {interaction.user.mention}",
                color=embed_color
            )
            await interaction.response.send_message(embed=embed)
            
            # Update button label
            self.label = "Unclaim"
            self.style = discord.ButtonStyle.secondary
            await interaction.edit_original_response(view=self.view)

class TranscriptButton(discord.ui.Button):
    def __init__(self, ticket_id: int, guild_id: str):
        super().__init__(
            label="Transcript",
            style=discord.ButtonStyle.secondary,
            emoji=ANIMATED_EMOJIS['file'],
            custom_id=f"transcript_{guild_id}_{ticket_id}"
        )
        self.ticket_id = ticket_id
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        config = load_guild_config(self.guild_id)
        if not config:
            await interaction.response.send_message("❌ Server not configured!", ephemeral=True)
            return

        is_staff = any(role.id in config["staff_role_ids"] for role in interaction.user.roles)
        if not is_staff:
            await interaction.response.send_message("❌ Only staff members can generate transcripts.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Generate enhanced transcript with full message data
        messages_data = []
        async for msg in interaction.channel.history(limit=None, oldest_first=True):
            # Get user avatar
            avatar_url = msg.author.avatar.url if msg.author.avatar else msg.author.default_avatar.url
            
            message_data = {
                'id': msg.id,
                'author': {
                    'id': msg.author.id,
                    'username': msg.author.name,
                    'display_name': msg.author.display_name,
                    'avatar_url': avatar_url,
                    'bot': msg.author.bot
                },
                'content': msg.content,
                'timestamp': msg.created_at,
                'embeds': [],
                'attachments': []
            }
            
            # Process embeds
            for embed in msg.embeds:
                embed_data = {
                    'title': embed.title,
                    'description': embed.description,
                    'color': embed.color.value if embed.color else None,
                    'fields': [{'name': field.name, 'value': field.value, 'inline': field.inline} for field in embed.fields],
                    'footer': embed.footer.text if embed.footer else None,
                    'thumbnail': embed.thumbnail.url if embed.thumbnail else None,
                    'image': embed.image.url if embed.image else None
                }
                message_data['embeds'].append(embed_data)
            
            # Process attachments
            for attachment in msg.attachments:
                attachment_data = {
                    'filename': attachment.filename,
                    'url': attachment.url,
                    'size': attachment.size
                }
                message_data['attachments'].append(attachment_data)
            
            messages_data.append(message_data)

        # Add ticket metadata
        tickets_data = load_guild_tickets(self.guild_id)
        ticket_info = tickets_data.get(str(self.ticket_id), {})

        # Create only HTML transcript with Discord styling
        html_content = await self.generate_discord_html_transcript(messages_data, ticket_info, interaction.guild, interaction.channel)
        
        # Create transcript file
        os.makedirs(f"transcripts/{self.guild_id}", exist_ok=True)
        html_filename = f"transcripts/{self.guild_id}/transcript_{self.ticket_id}_{int(time.time())}.html"
        
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Create a mobile-friendly text version
        text_content = await self.generate_mobile_friendly_transcript(messages_data, ticket_info, interaction.guild, interaction.channel)
        text_filename = f"transcripts/{self.guild_id}/transcript_{self.ticket_id}_{int(time.time())}.txt"
        
        with open(text_filename, "w", encoding="utf-8") as f:
            f.write(text_content)

        # Check if transcripts should be sent to users
        config = load_guild_config(self.guild_id)
        send_to_user = config.get("send_transcript_to_user", True)
        
        if send_to_user:
            # Send both HTML and text versions with user guidance
            embed = discord.Embed(
                title="<a:file:1401629622973759650> Transcript Generated Successfully",
                description="Choose your preferred format:",
                color=discord.Color.green()
            )
            embed.add_field(
                name="<a:laptop:1401636098098073720> Desktop Users",
                value="Download the HTML file for the best viewing experience with Discord styling",
                inline=False
            )
            embed.add_field(
                name="<a:mobile:1401636122282426529> Mobile Users", 
                value="Use the TXT file for easier mobile viewing and copying",
                inline=False
            )
            embed.add_field(
                name="<a:stats:1401587832526602240> Stats",
                value=f"**Messages:** {len(messages_data)}\n**File Size:** HTML (~{len(html_content)//1024}KB), TXT (~{len(text_content)//1024}KB)",
                inline=False
            )
            
            try:
                await interaction.followup.send(
                    embed=embed,
                    files=[discord.File(html_filename), discord.File(text_filename)],
                    ephemeral=True
                )
            except discord.HTTPException:
                # Fallback if files are too large
                await interaction.followup.send(
                    "<a:file:1401629622973759650> Transcript generated but files are too large to send directly. Check the transcripts directory.",
                    ephemeral=True
                )
        else:
            # Just confirm generation without sending files to user
            await interaction.followup.send(
                "<a:file:1401629622973759650> Transcript generated successfully and sent to log channel.",
                ephemeral=True
            )

        # Send transcripts to log channel
        config = load_guild_config(self.guild_id)
        if config and config.get("log_channel_id"):
            log_channel = interaction.guild.get_channel(config["log_channel_id"])
            if log_channel:
                try:
                    log_embed = discord.Embed(
                        title="<a:file:1401629622973759650> Transcript Generated",
                        description=f"Transcript for Ticket #{self.ticket_id}",
                        color=discord.Color.blue()
                    )
                    log_embed.add_field(name="Generated by", value=interaction.user.mention, inline=True)
                    log_embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
                    log_embed.add_field(name="Messages", value=str(len(messages_data)), inline=True)
                    
                    # Always send both HTML and TXT to log channel
                    await log_channel.send(
                        embed=log_embed,
                        files=[discord.File(html_filename), discord.File(text_filename)]
                    )
                except discord.HTTPException:
                    # Send a message if files are too large for log channel
                    await log_channel.send(
                        embed=log_embed.add_field(name="Note", value="Files too large for Discord - check transcripts directory", inline=False)
                    )
                except Exception as e:
                    print(f"Failed to send transcript to log channel: {e}")

    async def generate_discord_html_transcript(self, messages_data, ticket_info, guild, channel):
        """Generate Discord-styled HTML transcript"""
        
        # Get creator info
        creator_id = ticket_info.get('creator_id')
        creator = guild.get_member(creator_id) if creator_id else None
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket #{self.ticket_id} Transcript - {guild.name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&family=Whitney:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: "Whitney", "Helvetica Neue", Helvetica, Arial, "Noto Color Emoji", sans-serif;
            background: #36393f;
            color: #dcddde;
            line-height: 1.375;
            font-feature-settings: "liga" 1, "kern" 1;
            text-rendering: optimizeLegibility;
        }}
        
        .transcript-container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #36393f;
        }}
        
        .header {{
            background: #2f3136;
            padding: 15px;
            border-bottom: 1px solid #202225;
        }}
        
        .header h1 {{
            color: #ffffff;
            font-size: 24px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }}
        
        .ticket-icon {{
            background: #5865f2;
            color: white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            font-weight: bold;
        }}
        
        .header-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .info-item {{
            background: #40444b;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #5865f2;
        }}
        
        .info-label {{
            font-size: 12px;
            color: #b9bbbe;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        
        .info-value {{
            color: #ffffff;
            font-weight: 500;
        }}
        
        .messages {{
            padding: 20px;
        }}
        
        .message {{
            display: flex;
            margin-bottom: 20px;
            padding: 8px 0;
            position: relative;
        }}
        
        .message:hover {{
            background: rgba(4, 4, 5, 0.07);
            margin: 0 -20px 20px -20px;
            padding: 8px 20px;
            border-radius: 0;
        }}
        
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 16px;
            flex-shrink: 0;
            cursor: pointer;
        }}
        
        .message-content {{
            flex: 1;
            min-width: 0;
        }}
        
        .message-header {{
            display: flex;
            align-items: baseline;
            margin-bottom: 4px;
        }}
        
        .username {{
            font-weight: 500;
            color: #ffffff;
            margin-right: 8px;
            cursor: pointer;
        }}
        
        .username:hover {{
            text-decoration: underline;
        }}
        
        .bot-tag {{
            background: #5865f2;
            color: #ffffff;
            font-size: 10px;
            font-weight: 500;
            padding: 1px 4px;
            border-radius: 3px;
            margin-right: 8px;
            text-transform: uppercase;
        }}
        
        .timestamp {{
            font-size: 12px;
            color: #72767d;
            margin-left: 8px;
        }}
        
        .message-text {{
            color: #dcddde;
            word-wrap: break-word;
            white-space: pre-wrap;
            font-family: "Whitney", "Helvetica Neue", Helvetica, Arial, "Noto Color Emoji", sans-serif;
        }}
        
        .message-text strong {{
            font-weight: 600;
            color: #ffffff;
        }}
        
        .message-text em {{
            font-style: italic;
            color: #dcddde;
        }}
        
        .message-text code {{
            background: #2f3136;
            color: #f8f8f2;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", "Menlo", monospace;
            font-size: 85%;
        }}
        
        .message-text pre {{
            background: #2f3136;
            color: #f8f8f2;
            padding: 8px 12px;
            border-radius: 4px;
            border-left: 4px solid #40444b;
            font-family: "Consolas", "Monaco", "Menlo", monospace;
            font-size: 14px;
            line-height: 1.125;
            white-space: pre-wrap;
            overflow-x: auto;
            margin: 4px 0;
        }}
        
        .message-text .spoiler {{
            background: #202225;
            color: #202225;
            border-radius: 3px;
            padding: 0 2px;
            cursor: pointer;
            user-select: none;
        }}
        
        .message-text .spoiler:hover,
        .message-text .spoiler.revealed {{
            color: #dcddde;
            background: #484c52;
        }}
        
        .message-text .mention {{
            background: #414675;
            color: #dee0fc;
            padding: 0 2px;
            border-radius: 3px;
            font-weight: 500;
        }}
        
        .message-text .channel-mention {{
            background: #414675;
            color: #00b0f4;
            padding: 0 2px;
            border-radius: 3px;
            font-weight: 500;
        }}
        
        .message-text .role-mention {{
            background: #414675;
            color: #faa61a;
            padding: 0 2px;
            border-radius: 3px;
            font-weight: 500;
        }}
        
        .message-text .emoji {{
            width: 22px;
            height: 22px;
            vertical-align: middle;
            object-fit: contain;
            display: inline-block;
            border: none;
            background: transparent;
            margin: 0 1px;
        }}
        
        .message-text .emoji-large {{
            width: 48px;
            height: 48px;
            vertical-align: middle;
            object-fit: contain;
            display: inline-block;
            border: none;
            background: transparent;
            margin: 2px;
        }}
        
        .message-text .emoji:hover {{
            transform: scale(1.1);
            transition: transform 0.1s ease;
        }}
        
        .unicode-emoji {{
            font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Twemoji Mozilla", "Android Emoji", sans-serif;
            font-size: 1.2em;
            line-height: 1;
            vertical-align: middle;
        }}
        
        .emoji-fallback {{
            background: #40444b;
            color: #dcddde;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", "Menlo", monospace;
            font-size: 12px;
            font-weight: 500;
            border: 1px solid #5865f2;
            display: inline-block;
            vertical-align: middle;
            margin: 0 1px;
        }}
        
        .discord-header {{
            color: #ffffff;
            margin: 12px 0 8px 0;
            font-weight: 600;
        }}
        
        .discord-header h1 {{
            font-size: 20px;
        }}
        
        .discord-header h2 {{
            font-size: 18px;
        }}
        
        .discord-header h3 {{
            font-size: 16px;
        }}
        
        .code-block {{
            background: #2f3136;
            color: #f8f8f2;
            padding: 8px 12px;
            border-radius: 4px;
            border-left: 4px solid #40444b;
            font-family: "Consolas", "Monaco", "Menlo", "Courier New", monospace;
            font-size: 14px;
            line-height: 1.125;
            white-space: pre-wrap;
            overflow-x: auto;
            margin: 4px 0;
            position: relative;
        }}
        
        .code-block[data-lang]:not([data-lang=""]):before {{
            content: attr(data-lang);
            position: absolute;
            top: 2px;
            right: 8px;
            font-size: 10px;
            color: #72767d;
            text-transform: uppercase;
            font-weight: 600;
        }}
        
        .inline-code {{
            background: #2f3136;
            color: #f8f8f2;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", "Menlo", "Courier New", monospace;
            font-size: 85%;
        }}
        
        .quote-line {{
            background: #2f3136;
            border-left: 4px solid #4f545c;
            margin: 4px 0;
            padding: 8px 12px;
            border-radius: 0 4px 4px 0;
            color: #b5b6b8;
            font-style: italic;
            position: relative;
        }}
        
        .quote-line::before {{
            content: "▶ ";
            color: #72767d;
            font-weight: bold;
            font-style: normal;
        }}
        
        .discord-link {{
            color: #00b0f4;
            text-decoration: none;
            word-break: break-all;
        }}
        
        .discord-link:hover {{
            text-decoration: underline;
        }}
        
        .message-reply {{
            background: #2f3136;
            border-left: 4px solid #4f545c;
            margin: 4px 0;
            padding: 8px 12px;
            border-radius: 0 4px 4px 0;
            color: #b5b6b8;
            font-style: italic;
        }}
        
        .message-reply::before {{
            content: "↳ ";
            color: #72767d;
            font-weight: bold;
        }}
        
        .video-attachment {{
            max-width: 500px;
            border-radius: 8px;
            margin: 8px 0;
        }}
        
        .video-container {{
            position: relative;
            display: inline-block;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .video-controls {{
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px;
            font-size: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .image-attachment {{
            max-width: 500px;
            border-radius: 8px;
            margin: 8px 0;
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        
        .image-attachment:hover {{
            transform: scale(1.02);
        }}
        
        .media-modal {{
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            cursor: pointer;
        }}
        
        .media-modal img,
        .media-modal video {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
        }}
        
        .close-modal {{
            position: absolute;
            top: 20px;
            right: 30px;
            color: white;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            z-index: 10000;
        }}
        
        .close-modal:hover {{
            color: #ccc;
        }}
        
        .embed {{
            border-left: 4px solid #5865f2;
            background: #2f3136;
            margin: 8px 0;
            border-radius: 0 4px 4px 0;
            padding: 16px;
            max-width: 520px;
        }}
        
        .embed-title {{
            color: #00b0f4;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .embed-description {{
            color: #dcddde;
            font-size: 14px;
            line-height: 1.375;
            margin-bottom: 8px;
        }}
        
        .embed-field {{
            margin-bottom: 8px;
        }}
        
        .embed-field-name {{
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 2px;
        }}
        
        .embed-field-value {{
            color: #dcddde;
            font-size: 14px;
        }}
        
        .embed-footer {{
            color: #72767d;
            font-size: 12px;
            margin-top: 8px;
        }}
        
        .attachment {{
            background: #2f3136;
            border: 1px solid #40444b;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            max-width: 400px;
        }}
        
        .attachment-name {{
            color: #00b0f4;
            font-weight: 500;
            margin-bottom: 4px;
        }}
        
        .attachment-size {{
            color: #72767d;
            font-size: 12px;
        }}
        
        .button {{
            background: #5865f2;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            margin: 4px 8px 4px 0;
            cursor: pointer;
            display: inline-block;
        }}
        
        .button:hover {{
            background: #4752c4;
        }}
        
        .button.secondary {{
            background: #4f545c;
        }}
        
        .button.secondary:hover {{
            background: #5d6269;
        }}
        
        .button.danger {{
            background: #ed4245;
        }}
        
        .button.danger:hover {{
            background: #c03537;
        }}
        
        .button.success {{
            background: #3ba55d;
        }}
        
        .button.success:hover {{
            background: #2d7d32;
        }}
        
        .footer {{
            background: #2f3136;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #202225;
            margin-top: 40px;
        }}
        
        .footer-text {{
            color: #72767d;
            font-size: 14px;
        }}
        
        .footer-links {{
            margin-top: 10px;
        }}
        
        .footer-link {{
            color: #00b0f4;
            text-decoration: none;
            margin: 0 10px;
        }}
        
        .footer-link:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .header {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 18px;
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }}
            
            .ticket-icon {{
                width: 30px;
                height: 30px;
                margin-right: 8px;
            }}
            
            .header-info {{
                grid-template-columns: 1fr;
                gap: 8px;
                margin-top: 10px;
            }}
            
            .info-item {{
                padding: 8px;
            }}
            
            .info-label {{
                font-size: 11px;
            }}
            
            .info-value {{
                font-size: 13px;
                word-break: break-word;
            }}
            
            .messages {{
                padding: 10px 5px;
            }}
            
            .message {{
                margin-bottom: 15px;
            }}
            
            .avatar {{
                width: 32px;
                height: 32px;
                margin-right: 12px;
            }}
            
            .username {{
                font-size: 14px;
            }}
            
            .timestamp {{
                font-size: 11px;
            }}
            
            .message-text {{
                font-size: 14px;
                line-height: 1.4;
            }}
            
            .embed {{
                padding: 12px;
                max-width: 100%;
            }}
            
            .embed-title {{
                font-size: 15px;
            }}
            
            .embed-description {{
                font-size: 13px;
            }}
            
            .attachment {{
                max-width: 100%;
                padding: 12px;
            }}
            
            .message-reply {{
                padding: 6px 10px;
                margin: 2px 0;
                font-size: 13px;
            }}
        }}
    </style>
    <script>
        // Enhanced Discord markdown parser with emoji and reply support
        function parseDiscordMarkdown(text) {{
            if (!text || typeof text !== 'string') return '';
            
            // First preserve any existing HTML entities
            text = text.replace(/&/g, '&amp;')
                      .replace(/</g, '&lt;')
                      .replace(/>/g, '&gt;')
                      .replace(/"/g, '&quot;')
                      .replace(/'/g, '&#39;');
            
            // Handle code blocks first (triple backticks with language support)
            text = text.replace(/```([a-zA-Z]*)?\\n?([\\s\\S]*?)```/g, function(match, lang, code) {{
                return '<pre class="code-block" data-lang="' + (lang || '') + '">' + code.trim() + '</pre>';
            }});
            
            // Handle inline code (single backticks)
            text = text.replace(/`([^`\\n]+)`/g, '<code class="inline-code">$1</code>');
            
            // Handle Discord formatting with proper escaping
            // Bold (**text** or __text__)
            text = text.replace(/\\*\\*([^*\\n]+?)\\*\\*/g, '<strong>$1</strong>');
            text = text.replace(/(?<!_)__([^_\\n]+?)__(?!_)/g, '<strong>$1</strong>');
            
            // Italic (*text* or _text_) - be careful not to interfere with bold
            text = text.replace(/(?<!\\*)\\*([^*\\n]+?)\\*(?!\\*)/g, '<em>$1</em>');
            text = text.replace(/(?<!_)_([^_\\n]+?)_(?!_)/g, '<em>$1</em>');
            
            // Strikethrough (~~text~~)
            text = text.replace(/~~([^~\\n]+?)~~/g, '<s>$1</s>');
            
            // Spoilers (||text||)
            text = text.replace(/\\|\\|([^|\\n]+?)\\|\\|/g, '<span class="spoiler" onclick="this.classList.toggle(\\'revealed\\')">$1</span>');
            
            // Handle Discord mentions
            text = text.replace(/&lt;@!?(\\d+)&gt;/g, '<span class="mention">@User</span>');
            text = text.replace(/&lt;#(\\d+)&gt;/g, '<span class="channel-mention">#channel</span>');
            text = text.replace(/&lt;@&amp;(\\d+)&gt;/g, '<span class="role-mention">@role</span>');
            
            // Handle custom Discord emojis with animated support
            text = text.replace(/&lt;(a?):(\\w+):(\\d+)&gt;/g, function(match, animated, name, id) {{
                const extension = animated ? 'gif' : 'png';
                const emojiUrl = 'https://cdn.discordapp.com/emojis/' + id + '.' + extension;
                return '<img class="emoji" src="' + emojiUrl + '" alt=":' + name + ':" title=":' + name + '" loading="lazy" onerror="this.outerHTML=\\'&lt;:' + name + ':' + id + '&gt;\\'">';
            }});
            
            // Handle Discord headers (## text)
            text = text.replace(/^### (.+)$/gm, '<h3 class="discord-header">$1</h3>');
            text = text.replace(/^## (.+)$/gm, '<h2 class="discord-header">$1</h2>');
            text = text.replace(/^# (.+)$/gm, '<h1 class="discord-header">$1</h1>');
            
            // Handle quoted text/replies (> text)
            text = text.replace(/^&gt; (.+)$/gm, '<div class="quote-line">$1</div>');
            
            // Handle links (restore from HTML entities first)
            text = text.replace(/(https?:\\/\\/[^\\s&lt;&gt;]+)/g, '<a href="$1" target="_blank" class="discord-link">$1</a>');
            
            // Convert line breaks to HTML
            text = text.replace(/\\n/g, '<br>');
            
            return text;
        }}
        
        // Function to render Unicode emojis properly
        function enhanceUnicodeEmojis(text) {{
            // This function ensures Unicode emojis render properly
            // by wrapping them in spans with emoji font fallbacks
            const emojiRegex = abc
            return text.replace(emojiRegex, '<span class="unicode-emoji">$1</span>');
        }}
        
        // Media modal functions
        function openModal(src, type) {{
            const modal = document.getElementById('mediaModal');
            const modalContent = document.getElementById('modalContent');
            
            if (type === 'video') {{
                modalContent.innerHTML = `<video controls autoplay style="max-width: 90%; max-height: 90%;"><source src="${{src}}" type="video/mp4">Your browser does not support the video tag.</video>`;
            }} else {{
                modalContent.innerHTML = `<img src="${{src}}" style="max-width: 90%; max-height: 90%; object-fit: contain;">`;
            }}
            
            modal.style.display = 'block';
        }}
        
        function closeModal() {{
            document.getElementById('mediaModal').style.display = 'none';
        }}
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {{
            // Parse all message text for Discord markdown and emojis
            const messageTexts = document.querySelectorAll('.message-text');
            messageTexts.forEach(function(element) {{
                if (element.textContent && element.textContent.trim()) {{
                    const originalText = element.textContent;
                    let parsedText = parseDiscordMarkdown(originalText);
                    parsedText = enhanceUnicodeEmojis(parsedText);
                    element.innerHTML = parsedText;
                }}
            }});
            
            // Add retry mechanism for failed emoji images
            setTimeout(function() {{
                const failedEmojis = document.querySelectorAll('.emoji[src*="discordapp.com"]');
                failedEmojis.forEach(function(img) {{
                    if (img.naturalHeight === 0) {{
                        // Try alternative CDN or fallback
                        const originalSrc = img.src;
                        const emojiId = originalSrc.match(/emojis\\/(\\d+)\\./);
                        const emojiName = img.title.replace(/:/g, '');
                        
                        if (emojiId) {{
                            // Try webp format as fallback
                            const newSrc = originalSrc.replace(/\\.(png|gif)$/, '.webp');
                            img.src = newSrc;
                            
                            img.onerror = function() {{
                                // Final fallback to text
                                this.outerHTML = '<span class="emoji-fallback" title="' + emojiName + '">:' + emojiName + ':</span>';
                            }};
                        }}
                    }}
                }});
            }}, 2000);
            
            // Also process embed content
            const embedDescriptions = document.querySelectorAll('.embed-description, .embed-field-value');
            embedDescriptions.forEach(function(element) {{
                if (element.textContent && element.textContent.trim()) {{
                    const originalText = element.textContent;
                    let parsedText = parseDiscordMarkdown(originalText);
                    parsedText = enhanceUnicodeEmojis(parsedText);
                    element.innerHTML = parsedText;
                }}
            }});
            
            // Add click handlers for images and videos
            const images = document.querySelectorAll('.image-attachment');
            images.forEach(function(img) {{
                img.addEventListener('click', function() {{
                    openModal(this.src, 'image');
                }});
            }});
            
            const videos = document.querySelectorAll('.video-attachment');
            videos.forEach(function(video) {{
                video.addEventListener('click', function() {{
                    openModal(this.src, 'video');
                }});
            }});
            
            // Close modal when clicking outside
            document.getElementById('mediaModal').addEventListener('click', function(e) {{
                if (e.target === this) {{
                    closeModal();
                }}
            }});
            
            // Handle spoiler clicks
            const spoilers = document.querySelectorAll('.spoiler');
            spoilers.forEach(function(spoiler) {{
                spoiler.addEventListener('click', function() {{
                    this.classList.toggle('revealed');
                }});
            }});
        }});
    </script>
</head>
<body>
    <!-- Media Modal -->
    <div id="mediaModal" class="media-modal">
        <span class="close-modal" onclick="closeModal()">&times;</span>
        <div id="modalContent"></div>
    </div>
    <div class="transcript-container">
        <div class="header">
            <h1>
                <div class="ticket-icon">🎫</div>
                Ticket #{self.ticket_id} Transcript
            </h1>
            <div class="header-info">
                <div class="info-item">
                    <div class="info-label">Server</div>
                    <div class="info-value">{guild.name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Channel</div>
                    <div class="info-value">#{channel.name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Created By</div>
                    <div class="info-value">{creator.display_name if creator else 'Unknown User'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Type</div>
                    <div class="info-value">{ticket_info.get('button_name', 'Unknown')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Priority</div>
                    <div class="info-value">{ticket_info.get('priority', 'medium').title()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value">{ticket_info.get('status', 'open').title()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Messages</div>
                    <div class="info-value">{len(messages_data)}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Generated</div>
                    <div class="info-value">{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                </div>
            </div>
        </div>
        
        <div class="messages">
"""
        
        for msg_data in messages_data:
            author = msg_data['author']
            timestamp = msg_data['timestamp'].strftime('%m/%d/%Y %I:%M %p')
            
            html += f"""
            <div class="message">
                <img src="{author['avatar_url']}" alt="{author['display_name']}" class="avatar">
                <div class="message-content">
                    <div class="message-header">
                        <span class="username">{author['display_name']}</span>
                        {f'<span class="bot-tag">BOT</span>' if author['bot'] else ''}
                        <span class="timestamp">{timestamp}</span>
                    </div>
"""
            
            if msg_data['content']:
                # Process content for replies and preserve custom emojis
                content = msg_data["content"]
                
                # Check if this is a reply to another message
                if content.startswith('> '):
                    # Split reply quote from actual message
                    lines = content.split('\n')
                    reply_lines = []
                    message_lines = []
                    in_reply = True
                    
                    for line in lines:
                        if line.startswith('> ') and in_reply:
                            reply_lines.append(line)
                        else:
                            in_reply = False
                            message_lines.append(line)
                    
                    if reply_lines:
                        html += '<div class="message-reply">'
                        for reply_line in reply_lines:
                            # Escape HTML but preserve Discord emoji format
                            escaped_line = reply_line[2:].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html += f'{escaped_line}<br>'
                        html += '</div>'
                    
                    if message_lines:
                        remaining_content = '\\n'.join(message_lines).strip()
                        if remaining_content:
                            # Escape HTML but preserve Discord emoji format
                            escaped_content = remaining_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html += f'<div class="message-text">{escaped_content}</div>'
                else:
                    # Regular message - escape HTML entities but preserve Discord emoji format
                    escaped_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    html += f'<div class="message-text">{escaped_content}</div>'
            
            # Add embeds
            for embed in msg_data['embeds']:
                border_color = f"#{embed['color']:06x}" if embed['color'] else "#5865f2"
                
                html += f"""
                    <div class="embed" style="border-left-color: {border_color};">
"""
                
                if embed['title']:
                    html += f'<div class="embed-title">{embed["title"]}</div>'
                
                if embed['description']:
                    html += f'<div class="embed-description">{embed["description"]}</div>'
                
                for field in embed['fields']:
                    html += f"""
                        <div class="embed-field">
                            <div class="embed-field-name">{field['name']}</div>
                            <div class="embed-field-value">{field['value']}</div>
                        </div>
"""
                
                if embed['footer']:
                    html += f'<div class="embed-footer">{embed["footer"]}</div>'
                
                html += '</div>'
            
            # Add attachments with enhanced media support
            for attachment in msg_data['attachments']:
                size_mb = attachment['size'] / (1024 * 1024)
                filename = attachment['filename'].lower()
                
                if any(filename.endswith(ext) for ext in ['.mp4', '.webm', '.mov', '.avi', '.mkv']):
                    # Video attachment
                    html += f"""
                        <div class="attachment">
                            <div class="attachment-name">🎬 {attachment['filename']}</div>
                            <div class="attachment-size">{size_mb:.2f} MB</div>
                            <div class="video-container">
                                <video class="video-attachment" controls poster="" preload="metadata">
                                    <source src="{attachment['url']}" type="video/mp4">
                                    Your browser does not support the video tag.
                                </video>
                                <div class="video-controls">
                                    <span>Click to view in fullscreen</span>
                                    <a href="{attachment['url']}" target="_blank" style="color: #00b0f4;">Download</a>
                                </div>
                            </div>
                        </div>
"""
                elif any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    # Image attachment
                    html += f"""
                        <div class="attachment">
                            <div class="attachment-name">🖼️ {attachment['filename']}</div>
                            <div class="attachment-size">{size_mb:.2f} MB</div>
                            <img class="image-attachment" src="{attachment['url']}" alt="{attachment['filename']}" loading="lazy">
                        </div>
"""
                elif any(filename.endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
                    # Audio attachment
                    html += f"""
                        <div class="attachment">
                            <div class="attachment-name">🎵 {attachment['filename']}</div>
                            <div class="attachment-size">{size_mb:.2f} MB</div>
                            <audio controls style="width: 100%; margin-top: 8px;">
                                <source src="{attachment['url']}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                        </div>
"""
                else:
                    # Regular file attachment
                    html += f"""
                        <div class="attachment">
                            <div class="attachment-name">📎 {attachment['filename']}</div>
                            <div class="attachment-size">{size_mb:.2f} MB</div>
                            <a href="{attachment['url']}" target="_blank" style="color: #00b0f4; text-decoration: none;">📥 Download</a>
                        </div>
"""
            
            html += """
                </div>
            </div>
"""
        
        html += f"""
        </div>
        
        <div class="footer">
            <div class="footer-text">
                Discord Ticket Transcript • Generated by Enhanced Ticket Bot
            </div>
            <div class="footer-links">
                <a href="#" class="footer-link">🎫 Close Ticket</a>
                <a href="#" class="footer-link">🎯 Claim Ticket</a>
                <a href="#" class="footer-link">📄 Generate New Transcript</a>
                <a href="#" class="footer-link">✏️ Rename Channel</a>
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        return html

    async def generate_mobile_friendly_transcript(self, messages_data, ticket_info, guild, channel):
        """Generate mobile-friendly text transcript"""
        
        # Get creator info
        creator_id = ticket_info.get('creator_id')
        creator = guild.get_member(creator_id) if creator_id else None
        
        text = f"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                            DISCORD TICKET TRANSCRIPT                             ║
╚══════════════════════════════════════════════════════════════════════════════════╝

🎫 Ticket ID: #{self.ticket_id}
🏢 Server: {guild.name}
📍 Channel: #{channel.name}
👤 Created By: {creator.display_name if creator else 'Unknown User'}
🏷️ Type: {ticket_info.get('button_name', 'Unknown')}
⚡ Priority: {ticket_info.get('priority', 'medium').title()}
📊 Status: {ticket_info.get('status', 'open').title()}
📝 Total Messages: {len(messages_data)}
🕐 Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

{'='*80}
MESSAGE HISTORY
{'='*80}

"""
        
        for i, msg_data in enumerate(messages_data, 1):
            author = msg_data['author']
            timestamp = msg_data['timestamp'].strftime('%m/%d/%Y %I:%M %p')
            
            text += f"\n[{i:03d}] {timestamp}\n"
            text += f"👤 {author['display_name']}"
            if author['bot']:
                text += " [BOT]"
            text += f" (ID: {author['id']})\n"
            
            if msg_data['content']:
                # Clean up content for mobile viewing
                content = msg_data['content'].replace('```', '---').replace('`', '"')
                text += f"💬 {content}\n"
            
            # Add embed information
            for embed in msg_data['embeds']:
                if embed['title']:
                    text += f"📄 EMBED: {embed['title']}\n"
                if embed['description']:
                    desc = embed['description'][:200] + "..." if len(embed['description']) > 200 else embed['description']
                    text += f"   📝 {desc}\n"
            
            # Add attachment information
            for attachment in msg_data['attachments']:
                size_mb = attachment['size'] / (1024 * 1024)
                text += f"📎 ATTACHMENT: {attachment['filename']} ({size_mb:.2f} MB)\n"
                text += f"   🔗 {attachment['url']}\n"
            
            text += "-" * 40 + "\n"
        
        text += f"\n{'='*80}\n"
        text += f"END OF TRANSCRIPT • Generated by Enhanced Ticket Bot\n"
        text += f"{'='*80}"
        
        return text

class RenameTicketButton(discord.ui.Button):
    def __init__(self, ticket_id: int, guild_id: str):
        super().__init__(
            label="Rename",
            style=discord.ButtonStyle.secondary,
            emoji=ANIMATED_EMOJIS['setting'],
            custom_id=f"rename_ticket_{guild_id}_{ticket_id}"
        )
        self.ticket_id = ticket_id
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        config = load_guild_config(self.guild_id)
        if not config:
            await interaction.response.send_message("❌ Server not configured!", ephemeral=True)
            return

        is_staff = any(role.id in config["staff_role_ids"] for role in interaction.user.roles)
        if not is_staff:
            await interaction.response.send_message("❌ Only staff members can rename tickets.", ephemeral=True)
            return

        await interaction.response.send_modal(RenameModal(self.ticket_id, self.guild_id))

class RenameModal(discord.ui.Modal, title='Rename Ticket Channel'):
    new_name = discord.ui.TextInput(
        label='New channel name (no spaces, lowercase)', 
        placeholder="support-urgent-123",
        max_length=50
    )

    def __init__(self, ticket_id: int, guild_id: str):
        super().__init__()
        self.ticket_id = ticket_id
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.new_name.value.lower().replace(' ', '-')
        # Remove invalid characters
        new_name = re.sub(r'[^a-z0-9\-]', '', new_name)
        
        if not new_name:
            await interaction.response.send_message("❌ Invalid channel name!", ephemeral=True)
            return

        try:
            await interaction.channel.edit(name=new_name)
            embed = discord.Embed(
                title="✅ Channel Renamed",
                description=f"Channel renamed to `{new_name}` by {interaction.user.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to rename channels!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to rename channel: {str(e)}", ephemeral=True)

class ConfirmCloseView(discord.ui.View):
    def __init__(self, ticket_id: int, guild_id: str):
        super().__init__(timeout=60)
        self.ticket_id = ticket_id
        self.guild_id = guild_id
        self.add_item(ConfirmButton(ticket_id, guild_id))
        self.add_item(CancelButton())

class ConfirmButton(discord.ui.Button):
    def __init__(self, ticket_id: int, guild_id: str):
        super().__init__(emoji="✅", style=discord.ButtonStyle.success, label="Yes, Close Ticket")
        self.ticket_id = ticket_id
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        config = load_guild_config(self.guild_id)
        guild = interaction.guild
        tickets_data = load_guild_tickets(self.guild_id)
        ticket_info = tickets_data.get(str(self.ticket_id))

        if not ticket_info:
            await interaction.response.send_message("❌ Ticket data not found.", ephemeral=True)
            return

        channel = guild.get_channel(ticket_info["channel_id"])
        if not channel:
            await interaction.response.send_message("❌ Ticket channel not found.", ephemeral=True)
            return

        await interaction.response.defer()

        # Get all messages from the ticket channel
        messages = []
        async for msg in channel.history(limit=None, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            author_info = f"{msg.author.id}|{msg.author.name}|{msg.author.display_name}"
            
            if msg.content:
                messages.append(f"[{timestamp}] {author_info}: {msg.content}")
            
            for embed in msg.embeds:
                if embed.title:
                    messages.append(f"[{timestamp}] {author_info} sent embed: {embed.title}")
            
            for attachment in msg.attachments:
                messages.append(f"[{timestamp}] {author_info} sent attachment: {attachment.filename} ({attachment.url})")

        closed_at = datetime.datetime.utcnow().isoformat()
        
        # Create comprehensive summary
        summary = f"""
{'='*50}
TICKET CLOSURE SUMMARY
{'='*50}
Ticket ID: {self.ticket_id}
Created by: <@{ticket_info['creator_id']}>
Closed by: {interaction.user.mention}
Claimed by: <@{ticket_info.get('claimed_by', 'None')}>
Type: {ticket_info['button_name']}
Priority: {ticket_info.get('priority', 'Medium').title()}
Status: Closed
Reopened: {ticket_info['reopened']}
Total messages: {len(messages)}
Notes count: {len(ticket_info.get('notes', []))}
Added users: {len(ticket_info.get('added_users', []))}
Created at: {ticket_info['created_at']}
Closed at: {closed_at}
Duration: {self.calculate_duration(ticket_info['created_at'], closed_at)}
{'='*50}
"""
        
        log_content = "\n".join(messages) + "\n" + summary

        # Create logs directory for this guild
        os.makedirs(f"logs/{self.guild_id}", exist_ok=True)
        log_filename = f"logs/{self.guild_id}/ticket_{self.ticket_id}_{int(time.time())}.txt"
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(log_content)

        # Generate HTML and TXT transcripts for closing
        messages_data = []
        async for msg in channel.history(limit=None, oldest_first=True):
            # Get user avatar
            avatar_url = msg.author.avatar.url if msg.author.avatar else msg.author.default_avatar.url
            
            message_data = {
                'id': msg.id,
                'author': {
                    'id': msg.author.id,
                    'username': msg.author.name,
                    'display_name': msg.author.display_name,
                    'avatar_url': avatar_url,
                    'bot': msg.author.bot
                },
                'content': msg.content,
                'timestamp': msg.created_at,
                'embeds': [],
                'attachments': []
            }
            
            # Process embeds
            for embed in msg.embeds:
                embed_data = {
                    'title': embed.title,
                    'description': embed.description,
                    'color': embed.color.value if embed.color else None,
                    'fields': [{'name': field.name, 'value': field.value, 'inline': field.inline} for field in embed.fields],
                    'footer': embed.footer.text if embed.footer else None,
                    'thumbnail': embed.thumbnail.url if embed.thumbnail else None,
                    'image': embed.image.url if embed.image else None
                }
                message_data['embeds'].append(embed_data)
            
            # Process attachments
            for attachment in msg.attachments:
                attachment_data = {
                    'filename': attachment.filename,
                    'url': attachment.url,
                    'size': attachment.size
                }
                message_data['attachments'].append(attachment_data)
            
            messages_data.append(message_data)

        # Create HTML transcript
        from main import TranscriptButton
        transcript_button = TranscriptButton(self.ticket_id, self.guild_id)
        html_content = await transcript_button.generate_discord_html_transcript(messages_data, ticket_info, guild, channel)
        text_content = await transcript_button.generate_mobile_friendly_transcript(messages_data, ticket_info, guild, channel)
        
        # Create transcript files
        os.makedirs(f"transcripts/{self.guild_id}", exist_ok=True)
        html_filename = f"transcripts/{self.guild_id}/transcript_{self.ticket_id}_{int(time.time())}_close.html"
        text_filename = f"transcripts/{self.guild_id}/transcript_{self.ticket_id}_{int(time.time())}_close.txt"
        
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        with open(text_filename, "w", encoding="utf-8") as f:
            f.write(text_content)

        # Send comprehensive log to log channel
        log_channel = guild.get_channel(config["log_channel_id"])
        if log_channel:
            embed_color = get_embed_color(self.guild_id)
            embed = discord.Embed(
                title=f"🔒 Ticket Closed - #{self.ticket_id}",
                description=f"Ticket closed by {interaction.user.mention}",
                color=embed_color
            )
            
            creator = guild.get_member(ticket_info['creator_id'])
            claimer = guild.get_member(ticket_info.get('claimed_by')) if ticket_info.get('claimed_by') else None
            
            embed.add_field(name="👤 Created by", value=creator.mention if creator else f"<@{ticket_info['creator_id']}>", inline=True)
            embed.add_field(name="🏷️ Type", value=ticket_info['button_name'], inline=True)
            embed.add_field(name="⚡ Priority", value=ticket_info.get('priority', 'Medium').title(), inline=True)
            embed.add_field(name="🎯 Claimed by", value=claimer.mention if claimer else "None", inline=True)
            embed.add_field(name="🔄 Reopened", value=ticket_info['reopened'], inline=True)
            embed.add_field(name="📊 Messages", value=str(len(messages)), inline=True)
            embed.add_field(name="⏱️ Duration", value=self.calculate_duration(ticket_info['created_at'], closed_at), inline=True)
            embed.add_field(name="📝 Notes", value=str(len(ticket_info.get('notes', []))), inline=True)
            embed.add_field(name="👥 Added Users", value=str(len(ticket_info.get('added_users', []))), inline=True)
            
            embed.set_footer(text=f"Closed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

            try:
                # Send both HTML and TXT transcripts to log channel
                await log_channel.send(
                    embed=embed, 
                    files=[discord.File(html_filename), discord.File(text_filename), discord.File(log_filename)]
                )
            except discord.HTTPException:
                # Fallback if files are too large
                try:
                    await log_channel.send(embed=embed, file=discord.File(log_filename))
                except:
                    await log_channel.send(embed=embed)

        # Send transcript to user if enabled
        if config.get("send_transcript_to_user", True) and creator:
            try:
                dm_embed = discord.Embed(
                    title=f"🔒 Your Ticket Has Been Closed",
                    description=f"Your ticket #{self.ticket_id} in **{guild.name}** has been closed.",
                    color=embed_color
                )
                dm_embed.add_field(name="🏷️ Type", value=ticket_info['button_name'], inline=True)
                dm_embed.add_field(name="⏱️ Duration", value=self.calculate_duration(ticket_info['created_at'], closed_at), inline=True)
                dm_embed.add_field(name="📊 Messages", value=str(len(messages)), inline=True)
                dm_embed.add_field(
                    name="📄 Transcript Files",
                    value="Choose your preferred format:\n💻 **HTML** - Best for desktop viewing\n📱 **TXT** - Mobile-friendly format",
                    inline=False
                )
                
                await creator.send(
                    embed=dm_embed,
                    files=[discord.File(html_filename), discord.File(text_filename)]
                )
            except discord.Forbidden:
                # User has DMs disabled
                pass
            except Exception as e:
                print(f"Failed to send DM to user: {e}")

        # Update ticket data
        ticket_info["closed"] = True
        ticket_info["closed_at"] = closed_at
        ticket_info["closed_by"] = interaction.user.id
        ticket_info["status"] = "closed"
        tickets_data[str(self.ticket_id)] = ticket_info
        save_guild_tickets(self.guild_id, tickets_data)

        # Send closure message
        embed_color = get_embed_color(self.guild_id)
        closure_embed = discord.Embed(
            title="🔒 Ticket Closing",
            description=f"This ticket has been closed by {interaction.user.mention}.\n\nThe channel will be deleted in **10 seconds**.",
            color=embed_color
        )
        closure_embed.add_field(
            name="📊 Summary", 
            value=f"**Duration:** {self.calculate_duration(ticket_info['created_at'], closed_at)}\n**Messages:** {len(messages)}\n**Notes:** {len(ticket_info.get('notes', []))}", 
            inline=False
        )
        
        await channel.send(embed=closure_embed)
        await interaction.followup.send("✅ Ticket closed successfully. Channel will be deleted shortly.")

        # Wait and delete channel
        await asyncio.sleep(10)
        try:
            await channel.delete()
        except:
            pass

    def calculate_duration(self, start_time, end_time):
        """Calculate duration between start and end time"""
        try:
            start = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = end - start
            
            days = duration.days
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "Unknown"

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(emoji="❌", style=discord.ButtonStyle.secondary, label="Cancel")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Ticket close cancelled.", ephemeral=True)
        self.view.stop()

# ===== ERROR HANDLING =====

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors with user-friendly messages"""
    
    if isinstance(error, commands.CommandNotFound):
        # Get the attempted command
        command_name = ctx.message.content.split()[0][1:]  # Remove the prefix
        
        embed = discord.Embed(
            title="❌ Command Not Found",
            description=f"The command `{command_name}` doesn't exist.",
            color=discord.Color.red()
        )
        
        # Suggest similar commands
        available_commands = [cmd.name for cmd in bot.commands if not cmd.hidden]
        suggestions = []
        
        # Simple fuzzy matching
        for cmd in available_commands:
            if command_name.lower() in cmd.lower() or cmd.lower() in command_name.lower():
                suggestions.append(cmd)
        
        if suggestions:
            embed.add_field(
                name="💡 Did you mean?",
                value="\n".join([f"• `-{cmd}`" for cmd in suggestions[:3]]),
                inline=False
            )
        
        embed.add_field(
            name="📚 Need Help?",
            value="Use `-help` to see all available commands",
            inline=False
        )
        
        await ctx.send(embed=embed, delete_after=10)
        
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Required Argument",
            description=f"The command is missing a required argument: `{error.param.name}`",
            color=discord.Color.red()
        )
        embed.add_field(
            name="💡 Need Help?",
            value=f"Use `-help {ctx.command.name}` for usage information",
            inline=False
        )
        await ctx.send(embed=embed, delete_after=15)
        
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Missing Permissions",
            description="You don't have the required permissions to use this command.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Required Permissions",
            value=", ".join(error.missing_permissions),
            inline=False
        )
        await ctx.send(embed=embed, delete_after=10)
        
    elif isinstance(error, commands.CheckFailure):
        embed = discord.Embed(
            title="❌ Command Check Failed",
            description="You don't meet the requirements to use this command.",
            color=discord.Color.red()
        )
        
        # Check if it's a guild configuration issue
        if not is_guild_configured(str(ctx.guild.id)):
            embed.add_field(
                name="⚙️ Server Not Configured",
                value="An administrator needs to run `-setup` first!",
                inline=False
            )
        else:
            embed.add_field(
                name="💡 Possible Issues",
                value="• You might not be in a ticket channel\n• You might not have staff permissions\n• The server configuration might be incomplete",
                inline=False
            )
            
        await ctx.send(embed=embed, delete_after=15)
        
    else:
        # Log unexpected errors
        print(f"Unexpected error in {ctx.command}: {error}")
        embed = discord.Embed(
            title="❌ An Error Occurred",
            description="An unexpected error occurred. Please try again or contact support.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=10)

# ===== BOT EVENTS =====

@bot.event
async def on_ready():
    print(f"🎫 {bot.user} is now online!")
    print(f"📊 Connected to {len(bot.guilds)} servers")
    
    # Fix coroutine error by properly counting members
    try:
        all_members = []
        for guild in bot.guilds:
            all_members.extend(guild.members)
        unique_users = len(set(all_members))
        print(f"👥 Serving {unique_users} users")
    except Exception as e:
        print(f"⚠️ Could not count members: {e}")
        
    print("🔄 Multi-server ticket bot ready with enhanced features!")

    # Register persistent views for all configured guilds
    try:
        configs_dir = "configs"
        if os.path.exists(configs_dir):
            total_views = 0
            total_panels = 0
            for config_file in os.listdir(configs_dir):
                if config_file.endswith('.json'):
                    guild_id = config_file[:-5]  # Remove .json extension

                    # Register ticket control views for open tickets
                    tickets_data = load_guild_tickets(guild_id)
                    for ticket_id, ticket_info in tickets_data.items():
                        if not ticket_info.get("closed", False):
                            bot.add_view(TicketControlView(int(ticket_id), guild_id))
                            total_views += 1

                    # Register ticket panel views
                    panels_data = load_guild_panels(guild_id)
                    for panel_id, panel_info in panels_data.items():
                        try:
                            guild = bot.get_guild(int(guild_id))
                            if guild:
                                channel = guild.get_channel(panel_info["channel_id"])
                                if channel:
                                    # Try to get the message to ensure it still exists
                                    try:
                                        message = await channel.fetch_message(int(panel_id))
                                        if message:
                                            bot.add_view(TicketPanelView(panel_info["button_names"], guild_id))
                                            total_panels += 1
                                    except discord.NotFound:
                                        # Message was deleted, remove from saved data
                                        del panels_data[panel_id]
                                        save_guild_panels(guild_id, panels_data)
                        except Exception as panel_error:
                            print(f"❌ Error restoring panel {panel_id}: {panel_error}")

        print(f"✅ Loaded {total_views} persistent views")
        print(f"✅ Restored {total_panels} ticket panels")
    except Exception as e:
        print(f"❌ Error during view registration: {e}")

    # Start auto-close task if enabled
    auto_close_task.start()

@tasks.loop(hours=1)
async def auto_close_task():
    """Auto-close tickets after configured time"""
    try:
        configs_dir = "configs"
        if not os.path.exists(configs_dir):
            return
            
        for config_file in os.listdir(configs_dir):
            if not config_file.endswith('.json'):
                continue
                
            guild_id = config_file[:-5]
            config = load_guild_config(guild_id)
            
            if not config or not config.get("auto_close_hours", 0):
                continue
                
            auto_close_hours = config["auto_close_hours"]
            tickets_data = load_guild_tickets(guild_id)
            
            for ticket_id, ticket_info in tickets_data.items():
                if ticket_info.get("closed", False):
                    continue
                    
                # Check if ticket is old enough to auto-close
                created_at = datetime.datetime.fromisoformat(ticket_info["created_at"])
                now = datetime.datetime.utcnow()
                hours_old = (now - created_at).total_seconds() / 3600
                
                if hours_old >= auto_close_hours:
                    guild = bot.get_guild(int(guild_id))
                    if not guild:
                        continue
                        
                    channel = guild.get_channel(ticket_info["channel_id"])
                    if not channel:
                        continue
                        
                    # Auto-close the ticket
                    embed = discord.Embed(
                        title="🕐 Auto-Close Notice",
                        description=f"This ticket has been automatically closed due to inactivity ({auto_close_hours} hours).",
                        color=discord.Color.orange()
                    )
                    
                    try:
                        await channel.send(embed=embed)
                        await asyncio.sleep(5)
                        
                        # Update ticket data
                        ticket_info["closed"] = True
                        ticket_info["closed_at"] = datetime.datetime.utcnow().isoformat()
                        ticket_info["closed_by"] = bot.user.id
                        ticket_info["auto_closed"] = True
                        tickets_data[ticket_id] = ticket_info
                        save_guild_tickets(guild_id, tickets_data)
                        
                        await channel.delete()
                    except:
                        continue
                        
    except Exception as e:
        print(f"Error in auto-close task: {e}")

# ===== HELPER FUNCTIONS =====

def guild_configured_check():
    """Check if the guild is configured"""
    async def predicate(ctx):
        guild_id = str(ctx.guild.id)
        if not is_guild_configured(guild_id):
            embed = discord.Embed(
                title="❌ Server Not Configured",
                description="This server needs to be set up first!\n\nAn administrator must run: `-setup <category_id> <log_channel_id> <staff_role_id>`",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Need Help?", 
                value="Run `-help setup` for detailed instructions.", 
                inline=False
            )
            await ctx.send(embed=embed)
            return False
        return True
    return commands.check(predicate)

async def is_ticket_channel(ctx):
    """Check if the current channel is a ticket channel"""
    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    if not config:
        return False

    if ctx.channel.category and ctx.channel.category.id == config["ticket_category_id"]:
        return True
    return False

def is_staff_member():
    """Check if user has any of the configured staff roles"""
    async def predicate(ctx):
        guild_id = str(ctx.guild.id)
        config = load_guild_config(guild_id)
        if not config:
            return False
        staff_role_ids = config.get("staff_role_ids", [])
        return any(role.id in staff_role_ids for role in ctx.author.roles)
    return commands.check(predicate)

# ===== SETUP COMMANDS =====

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx, category_id: int = None, log_channel_id: int = None, *staff_role_ids):
    """
    Setup the bot for this server.
    Usage: -setup <category_id> <log_channel_id> <staff_role_id1> [staff_role_id2] ...
    """
    # Provide detailed guidance if missing arguments
    if category_id is None or log_channel_id is None:
        embed = discord.Embed(
            title="❌ Missing Required Arguments",
            description="The setup command requires specific parameters to configure the bot properly.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="📋 Correct Usage",
            value="```-setup <category_id> <log_channel_id> <staff_role_id>```",
            inline=False
        )
        embed.add_field(
            name="🔍 How to Get IDs",
            value="1. Enable Developer Mode in Discord Settings\n2. Right-click on channels/roles\n3. Select 'Copy ID'",
            inline=False
        )
        embed.add_field(
            name="📝 Example",
            value="```-setup 123456789012345678 987654321098765432 555666777888999111```",
            inline=False
        )
        embed.add_field(
            name="💡 What You Need",
            value="• **Category ID**: Where ticket channels will be created\n• **Log Channel ID**: Where ticket logs will be sent\n• **Staff Role ID(s)**: Roles that can manage tickets",
            inline=False
        )
        await ctx.send(embed=embed)
        return
        
    if not staff_role_ids:
        embed = discord.Embed(
            title="❌ No Staff Roles Provided",
            description="You must provide at least one staff role ID.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="📝 Example",
            value="```-setup 123456789012345678 987654321098765432 555666777888999111```",
            inline=False
        )
        await ctx.send(embed=embed)
        return

    guild_id = str(ctx.guild.id)

    # Validate category
    category = ctx.guild.get_channel(category_id)
    if not category or not isinstance(category, discord.CategoryChannel):
        await ctx.send("❌ Invalid category ID! Please provide a valid category channel ID.")
        return

    # Validate log channel
    log_channel = ctx.guild.get_channel(log_channel_id)
    if not log_channel or not isinstance(log_channel, discord.TextChannel):
        await ctx.send("❌ Invalid log channel ID! Please provide a valid text channel ID.")
        return

    # Validate staff roles
    valid_roles = []
    for role_id in staff_role_ids:
        try:
            role_id_int = int(role_id)
            role = ctx.guild.get_role(role_id_int)
            if role:
                valid_roles.append(role_id_int)
            else:
                await ctx.send(f"⚠️ Warning: Role ID {role_id} not found!")
        except ValueError:
            await ctx.send(f"⚠️ Warning: Invalid role ID format: {role_id}")

    if not valid_roles:
        await ctx.send("❌ No valid staff roles provided!")
        return

    # Create directories
    for directory in ["configs", "tickets", "blacklists", "warnings", "tags", "panels", f"logs/{guild_id}", f"transcripts/{guild_id}"]:
        os.makedirs(directory, exist_ok=True)

    config_data = {
        "ticket_category_id": category_id,
        "log_channel_id": log_channel_id,
        "staff_role_ids": valid_roles,
        "embed_color": [128, 0, 255],
        "command_prefix": "-",
        "welcome_message": "**Welcome {user}!** 👋\n\nThank you for creating a ticket. Our support team will be with you shortly.\nPlease provide any additional details about your issue while you wait.",
        "auto_close_hours": 72,
        "max_tickets_per_user": 3,
        "send_transcript_to_user": True,
        "setup_by": ctx.author.id,
        "setup_at": datetime.datetime.utcnow().isoformat(),
        "version": "6.0-enhanced"
    }

    save_guild_config(guild_id, config_data)

    embed = discord.Embed(
        title="✅ Bot Setup Complete",
        description=f"**Enhanced Ticket Bot** has been configured for **{ctx.guild.name}**",
        color=discord.Color.green()
    )
    embed.add_field(name="🏷️ Ticket Category", value=f"{category.mention}", inline=True)
    embed.add_field(name="📝 Log Channel", value=f"{log_channel.mention}", inline=True)
    embed.add_field(name="👮 Staff Roles", value=f"{len(valid_roles)} roles configured", inline=True)
    embed.add_field(name="🎫 Max Tickets/User", value="3", inline=True)
    embed.add_field(name="⏰ Auto-Close", value="72 hours", inline=True)
    embed.add_field(name="🎨 Theme", value="Default Purple", inline=True)
    embed.add_field(
        name="🚀 Next Steps", 
        value="• Use `-panel #channel Button1 Button2` to create a ticket panel\n• Use `-config` to customize settings\n• Use `-help` to see all commands", 
        inline=False
    )
    embed.set_footer(text=f"Setup by {ctx.author} • Enhanced Bot v6.0", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

@bot.command()
@guild_configured_check()
@commands.has_permissions(administrator=True)
async def config(ctx, setting: str = None, *, value: str = None):
    """
    View or modify server configuration.
    Usage: -config [setting] [value]
    Settings: auto_close_hours, max_tickets_per_user, welcome_message
    """
    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    
    if not setting:
        # Display current configuration
        embed = discord.Embed(
            title="⚙️ Server Configuration",
            description=f"Configuration for **{ctx.guild.name}**",
            color=get_embed_color(guild_id)
        )
        
        category = ctx.guild.get_channel(config["ticket_category_id"])
        log_channel = ctx.guild.get_channel(config["log_channel_id"])
        
        embed.add_field(name="🏷️ Ticket Category", value=category.mention if category else "❌ Not found", inline=True)
        embed.add_field(name="📝 Log Channel", value=log_channel.mention if log_channel else "❌ Not found", inline=True)
        embed.add_field(name="👮 Staff Roles", value=f"{len(config['staff_role_ids'])} roles", inline=True)
        embed.add_field(name="⏰ Auto-Close", value=f"{config.get('auto_close_hours', 0)} hours" if config.get('auto_close_hours') else "Disabled", inline=True)
        embed.add_field(name="🎫 Max Tickets/User", value=str(config.get('max_tickets_per_user', 3)), inline=True)
        embed.add_field(name="🎨 Embed Color", value=f"RGB({', '.join(map(str, config['embed_color']))})", inline=True)
        
        embed.add_field(
            name="💬 Welcome Message", 
            value=f"```{config.get('welcome_message', 'Default')[:100]}{'...' if len(config.get('welcome_message', '')) > 100 else ''}```", 
            inline=False
        )
        
        embed.add_field(name="📄 Send Transcript to User", value="✅ Enabled" if config.get('send_transcript_to_user', True) else "❌ Disabled", inline=True)
        
        embed.add_field(
            name="📊 Available Settings",
            value="• `auto_close_hours` - Auto-close after X hours (0 = disabled)\n• `max_tickets_per_user` - Max open tickets per user\n• `welcome_message` - Custom welcome message\n• `send_transcript_to_user` - Toggle transcript sending to users (true/false)",
            inline=False
        )
        
        await ctx.send(embed=embed)
        return
    
    if not value:
        await ctx.send(f"❌ Please provide a value for `{setting}`")
        return
    
    # Update specific settings
    if setting == "auto_close_hours":
        try:
            hours = int(value)
            if hours < 0:
                raise ValueError
            config["auto_close_hours"] = hours
            save_guild_config(guild_id, config)
            await ctx.send(f"✅ Auto-close set to {hours} hours {'(disabled)' if hours == 0 else ''}")
        except ValueError:
            await ctx.send("❌ Please provide a valid number of hours (0 or positive integer)")
    
    elif setting == "max_tickets_per_user":
        try:
            max_tickets = int(value)
            if max_tickets < 1 or max_tickets > 10:
                raise ValueError
            config["max_tickets_per_user"] = max_tickets
            save_guild_config(guild_id, config)
            await ctx.send(f"✅ Maximum tickets per user set to {max_tickets}")
        except ValueError:
            await ctx.send("❌ Please provide a number between 1 and 10")
    
    elif setting == "welcome_message":
        config["welcome_message"] = value
        save_guild_config(guild_id, config)
        embed = discord.Embed(
            title="✅ Welcome Message Updated",
            description="New welcome message:",
            color=get_embed_color(guild_id)
        )
        embed.add_field(name="Message", value=f"```{value}```", inline=False)
        embed.add_field(name="💡 Tip", value="Use `{user}` to mention the ticket creator", inline=False)
        await ctx.send(embed=embed)
    
    elif setting == "send_transcript_to_user":
        if value.lower() in ["true", "yes", "on", "enable", "enabled"]:
            config["send_transcript_to_user"] = True
            await ctx.send("✅ Transcript sending to users **enabled**")
        elif value.lower() in ["false", "no", "off", "disable", "disabled"]:
            config["send_transcript_to_user"] = False
            await ctx.send("✅ Transcript sending to users **disabled**")
        else:
            await ctx.send("❌ Please use `true` or `false` for this setting")
            return
        save_guild_config(guild_id, config)
    
    else:
        await ctx.send(f"❌ Unknown setting: `{setting}`\nAvailable: `auto_close_hours`, `max_tickets_per_user`, `welcome_message`, `send_transcript_to_user`")

@bot.command()
@guild_configured_check()
@commands.has_permissions(administrator=True)
async def panel(ctx, channel: discord.TextChannel = None, button1: str = None, button2: str = None, button3: str = None, button4: str = None, button5: str = None):
    """
    Creates a ticket panel with custom styling.
    Usage: -panel #channel Button1Name [Button2Name] [Button3Name] [Button4Name] [Button5Name]
    """
    if not channel or not button1:
        await ctx.send("❌ Please provide a channel and at least one button name.\nExample: `-panel #support Support Billing Technical Reports Bug-Report`")
        return

    guild_id = str(ctx.guild.id)
    button_names = [name for name in (button1, button2, button3, button4, button5) if name]

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title=f"{ANIMATED_EMOJIS['ticket']} Create Support Ticket",
        description="Need help? Click one of the buttons below to create a support ticket.\n\n**Choose the category that best describes your issue:**",
        color=embed_color
    )
    
    # Add button descriptions
    button_descriptions = {
        "Support": f"{ANIMATED_EMOJIS['setting']} General support and questions",
        "Billing": f"{ANIMATED_EMOJIS['stats']} Payment and subscription issues", 
        "Technical": f"{ANIMATED_EMOJIS['laptop']} Technical problems and bugs",
        "Reports": f"{ANIMATED_EMOJIS['file']} Report users or content",
        "Bug-Report": f"{ANIMATED_EMOJIS['zap']} Report bugs and glitches",
        "Appeals": f"{ANIMATED_EMOJIS['securepolice']} Appeal bans or warnings",
        "Partnership": f"{ANIMATED_EMOJIS['sparkle']} Partnership inquiries",
        "Other": f"{ANIMATED_EMOJIS['lightbulb']} Other issues not listed above"
    }
    
    description_text = ""
    for button in button_names:
        desc = button_descriptions.get(button, f"📝 {button} related issues")
        description_text += f"{desc}\n"
    
    embed.add_field(name="📋 Available Categories", value=description_text, inline=False)
    embed.add_field(
        name="ℹ️ Before Creating a Ticket", 
        value="• Check if your question is answered in our FAQ\n• Be descriptive about your issue\n• Provide relevant screenshots if needed\n• Be patient while waiting for support",
        inline=False
    )
    
    embed.set_footer(
        text=f"Support Team • {ctx.guild.name}", 
        icon_url=ctx.guild.icon.url if ctx.guild.icon else None
    )

    view = TicketPanelView(button_names, guild_id)
    panel_message = await channel.send(embed=embed, view=view)

    # Save panel data for persistence
    panels_data = load_guild_panels(guild_id)
    panels_data[str(panel_message.id)] = {
        "channel_id": channel.id,
        "button_names": button_names,
        "created_by": ctx.author.id,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    save_guild_panels(guild_id, panels_data)

    success_embed = discord.Embed(
        title="✅ Ticket Panel Created",
        description=f"Ticket panel successfully created in {channel.mention}",
        color=embed_color
    )
    success_embed.add_field(name="🎯 Buttons", value=f"{len(button_names)} categories configured", inline=True)
    success_embed.add_field(name="📍 Message ID", value=f"`{panel_message.id}`", inline=True)
    await ctx.send(embed=success_embed, delete_after=15)

    try:
        await ctx.message.delete()
    except:
        pass

# ===== TICKET MANAGEMENT COMMANDS =====

@bot.command()
@guild_configured_check()
@commands.check(is_ticket_channel)
async def close(ctx, *, reason: str = None):
    """
    Closes the current ticket channel with optional reason.
    Usage: -close [reason]
    This command can only be used within a ticket channel.
    """
    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    tickets_data = load_guild_tickets(guild_id)

    ticket_id = None
    for tid, data in tickets_data.items():
        if data["channel_id"] == ctx.channel.id:
            ticket_id = tid
            break

    if not ticket_id:
        await ctx.send("❌ Could not find ticket information for this channel.")
        return

    ticket_info = tickets_data[ticket_id]
    is_staff = any(role.id in config["staff_role_ids"] for role in ctx.author.roles)
    is_creator = ctx.author.id == ticket_info["creator_id"]

    if not (is_staff or is_creator):
        await ctx.send("❌ You do not have permission to close this ticket.")
        return

    # Add close reason if provided
    if reason:
        ticket_info["close_reason"] = reason
        tickets_data[ticket_id] = ticket_info
        save_guild_tickets(guild_id, tickets_data)

    view = ConfirmCloseView(int(ticket_id), guild_id)
    embed = discord.Embed(
        title="⚠️ Confirm Ticket Closure",
        description="Are you sure you want to close this ticket?\n\n**This action will:**\n• Archive all messages\n• Send logs to staff\n• Delete the channel after 10 seconds",
        color=discord.Color.orange()
    )
    
    if reason:
        embed.add_field(name="📝 Reason", value=f"```{reason}```", inline=False)
    
    await ctx.send(embed=embed, view=view)

@bot.group(invoke_without_command=True)
@guild_configured_check()
@is_staff_member()
@commands.check(is_ticket_channel)
async def priority(ctx):
    """
    Manage ticket priority.
    This command can only be used within a ticket channel by staff members.
    """
    await ctx.send_help(ctx.command)

@priority.command()
@guild_configured_check()
@is_staff_member()
@commands.check(is_ticket_channel)
async def set(ctx, level: str = None):
    """
    Set the priority of the current ticket.
    Usage: -priority set <high|medium|low>
    This command can only be used within a ticket channel by staff members.
    """
    if not level or level.lower() not in ["high", "medium", "low"]:
        await ctx.send("❌ Please specify a valid priority level: `high`, `medium`, or `low`.")
        return

    guild_id = str(ctx.guild.id)
    tickets_data = load_guild_tickets(guild_id)

    ticket_id = None
    for tid, data in tickets_data.items():
        if data["channel_id"] == ctx.channel.id:
            ticket_id = tid
            break

    if not ticket_id:
        await ctx.send("❌ Could not find ticket information for this channel.")
        return

    ticket_info = tickets_data[ticket_id]
    ticket_info["priority"] = level.lower()
    tickets_data[ticket_id] = ticket_info
    save_guild_tickets(guild_id, tickets_data)

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="✅ Priority Updated",
        description=f"Ticket priority set to `{level.title()}` by {ctx.author.mention}",
        color=embed_color
    )
    await ctx.send(embed=embed)

@priority.command()
@guild_configured_check()
@is_staff_member()
@commands.check(is_ticket_channel)
async def show(ctx):
    """
    Show the current priority of the ticket.
    This command can only be used within a ticket channel by staff members.
    """
    guild_id = str(ctx.guild.id)
    tickets_data = load_guild_tickets(guild_id)

    ticket_id = None
    for tid, data in tickets_data.items():
        if data["channel_id"] == ctx.channel.id:
            ticket_id = tid
            break

    if not ticket_id:
        await ctx.send("❌ Could not find ticket information for this channel.")
        return

    ticket_info = tickets_data[ticket_id]
    priority_level = ticket_info.get("priority", "medium").title()

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="🎫 Ticket Priority",
        description=f"The current priority for this ticket is: `{priority_level}`",
        color=embed_color
    )
    await ctx.send(embed=embed)

@bot.group(invoke_without_command=True)
@guild_configured_check()
@is_staff_member()
@commands.check(is_ticket_channel)
async def note(ctx):
    """
    Manage ticket notes.
    This command can only be used within a ticket channel by staff members.
    """
    await ctx.send_help(ctx.command)

@note.command()
@guild_configured_check()
@is_staff_member()
@commands.check(is_ticket_channel)
async def add(ctx, *, content: str = None):
    """
    Add a note to the current ticket.
    Usage: -note add Your note here
    This command can only be used within a ticket channel by staff members.
    """
    if not content:
        await ctx.send("❌ Please provide a note to add. Usage: `-note add Your note here`")
        return

    guild_id = str(ctx.guild.id)
    tickets_data = load_guild_tickets(guild_id)

    ticket_id = None
    for tid, data in tickets_data.items():
        if data["channel_id"] == ctx.channel.id:
            ticket_id = tid
            break

    if not ticket_id:
        await ctx.send("❌ Could not find ticket information for this channel.")
        return

    ticket_info = tickets_data[ticket_id]
    notes = ticket_info.get("notes", [])
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    notes.append({"author": ctx.author.id, "content": content, "timestamp": timestamp})
    ticket_info["notes"] = notes
    tickets_data[ticket_id] = ticket_info
    save_guild_tickets(guild_id, tickets_data)

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="📝 Note Added",
        description=f"A new note has been added to this ticket by {ctx.author.mention}",
        color=embed_color
    )
    embed.add_field(name="Note", value=f"```{content[:200]}{'...' if len(content) > 200 else ''}```", inline=False)
    await ctx.send(embed=embed)

@note.command()
@guild_configured_check()
@is_staff_member()
@commands.check(is_ticket_channel)
async def view(ctx):
    """
    View the last 10 notes for the current ticket.
    This command can only be used within a ticket channel by staff members.
    """
    guild_id = str(ctx.guild.id)
    tickets_data = load_guild_tickets(guild_id)

    ticket_id = None
    for tid, data in tickets_data.items():
        if data["channel_id"] == ctx.channel.id:
            ticket_id = tid
            break

    if not ticket_id:
        await ctx.send("❌ Could not find ticket information for this channel.")
        return

    ticket_info = tickets_data[ticket_id]
    notes = ticket_info.get("notes", [])
    if not notes:
        await ctx.send("❌ No notes found for this ticket.")
        return

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="📝 Ticket Notes",
        description=f"Last {min(10, len(notes))} notes for this ticket",
        color=embed_color
    )

    for note in notes[-10:]:  # Show last 10 notes
        author = ctx.guild.get_member(note['author'])
        author_name = author.display_name if author else "Unknown"
        timestamp = note['timestamp']
        embed.add_field(
            name=f"Note by {author_name}",
            value=f"```{note['content'][:100]}{'...' if len(note['content']) > 100 else ''}```\n*{timestamp}*",
            inline=False
        )

    embed.set_footer(text=f"Showing {min(10, len(notes))} of {len(notes)} notes")
    await ctx.send(embed=embed, ephemeral=True)

@bot.command()
@guild_configured_check()
@is_staff_member()
async def blacklist(ctx, user: discord.Member = None):
    """
    Add a user to the blacklist, preventing them from creating tickets.
    Usage: -blacklist @user
    This command can only be used by staff members.
    """
    if not user:
        await ctx.send("❌ Please specify a user to blacklist. Usage: `-blacklist @user`")


@bot.command()
@guild_configured_check()
@commands.has_permissions(administrator=True)
async def transcripttoggle(ctx):
    """
    Toggle whether transcripts are sent to users who opened tickets.
    Usage: -transcripttoggle
    This command can only be used by administrators.
    """
    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    
    current_setting = config.get("send_transcript_to_user", True)
    new_setting = not current_setting
    
    config["send_transcript_to_user"] = new_setting
    save_guild_config(guild_id, config)
    
    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="📄 Transcript Setting Updated",
        description=f"Transcript sending to users is now {'**enabled**' if new_setting else '**disabled**'}",
        color=embed_color
    )
    
    if new_setting:
        embed.add_field(
            name="✅ Enabled",
            value="Users who open tickets will receive both HTML and TXT transcripts when tickets are closed or when staff generate them",
            inline=False
        )
    else:
        embed.add_field(
            name="❌ Disabled", 
            value="Transcripts will only be sent to the log channel (both HTML and TXT), not to users",
            inline=False
        )
    
    embed.set_footer(text=f"Changed by {ctx.author}")
    await ctx.send(embed=embed)
    return
    guild_id = str(ctx.guild.id)
    blacklist = load_guild_blacklist(guild_id)

    if user.id in blacklist:
        await ctx.send(f"❌ {user.mention} is already blacklisted.")
        return

    blacklist.append(user.id)
    save_guild_blacklist(guild_id, blacklist)

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="🚫 User Blacklisted",
        description=f"{user.mention} has been blacklisted from creating tickets.",
        color=embed_color
    )
    embed.set_footer(text=f"Blacklisted by {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
@guild_configured_check()
@is_staff_member()
async def unblacklist(ctx, user: discord.Member = None):
    """
    Remove a user from the blacklist.
    Usage: -unblacklist @user
    This command can only be used by staff members.
    """
    if not user:
        await ctx.send("❌ Please specify a user to unblacklist. Usage: `-unblacklist @user`")
        return

    guild_id = str(ctx.guild.id)
    blacklist = load_guild_blacklist(guild_id)

    if user.id not in blacklist:
        await ctx.send(f"❌ {user.mention} is not blacklisted.")
        return

    blacklist.remove(user.id)
    save_guild_blacklist(guild_id, blacklist)

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="✅ User Unblacklisted",
        description=f"{user.mention} has been removed from the blacklist.",
        color=embed_color
    )
    embed.set_footer(text=f"Unblacklisted by {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
@guild_configured_check()
@is_staff_member()
async def ticketstats(ctx):
    """
    Display server ticket statistics.
    This command can only be used by staff members.
    """
    guild_id = str(ctx.guild.id)
    tickets_data = load_guild_tickets(guild_id)

    if not tickets_data:
        await ctx.send("📊 No ticket data found for this server.")
        return

    total_tickets = len(tickets_data)
    open_tickets = sum(1 for ticket in tickets_data.values() if not ticket.get("closed", False))
    closed_tickets = total_tickets - open_tickets
    claimed_tickets = sum(1 for ticket in tickets_data.values() if ticket.get("claimed_by"))

    # Priority breakdown
    high_priority = sum(1 for ticket in tickets_data.values() if ticket.get("priority") == "high" and not ticket.get("closed", False))
    medium_priority = sum(1 for ticket in tickets_data.values() if ticket.get("priority") == "medium" and not ticket.get("closed", False))
    low_priority = sum(1 for ticket in tickets_data.values() if ticket.get("priority") == "low" and not ticket.get("closed", False))

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="📊 Ticket Statistics",
        description=f"Statistics for **{ctx.guild.name}**",
        color=embed_color
    )

    embed.add_field(name="📋 Total Tickets", value=f"```{total_tickets}```", inline=True)
    embed.add_field(name="🔓 Open Tickets", value=f"```{open_tickets}```", inline=True)
    embed.add_field(name="🔒 Closed Tickets", value=f"```{closed_tickets}```", inline=True)
    embed.add_field(name="🎯 Claimed Tickets", value=f"```{claimed_tickets}```", inline=True)
    embed.add_field(name="🔴 High Priority", value=f"```{high_priority}```", inline=True)
    embed.add_field(name="🟡 Medium Priority", value=f"```{medium_priority}```", inline=True)
    embed.add_field(name="🟢 Low Priority", value=f"```{low_priority}```", inline=True)

    # Blacklist count
    blacklist = load_guild_blacklist(guild_id)
    embed.add_field(name="🚫 Blacklisted Users", value=f"```{len(blacklist)}```", inline=True)

    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed)

@bot.command()
@guild_configured_check()
@commands.has_permissions(administrator=True)
async def setcolor(ctx, hex_color: str = None):
    """
    Set the embed color for the server.
    Usage: -setcolor #FF5733
    This command can only be used by administrators.
    """
    if not hex_color:
        await ctx.send("❌ Please provide a hex color code. Example: `-setcolor #FF5733`")
        return

    # Remove # if present and validate
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        await ctx.send("❌ Invalid hex color format. Please use format: `#FF5733`")
        return

    try:
        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    except ValueError:
        await ctx.send("❌ Invalid hex color code.")
        return

    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    config["embed_color"] = [r, g, b]
    save_guild_config(guild_id, config)

    embed = discord.Embed(
        title="🎨 Color Updated",
        description=f"Server embed color has been updated!",
        color=discord.Color.from_rgb(r, g, b)
    )
    embed.add_field(name="New Color", value=f"```#{hex_color.upper()}```", inline=True)
    embed.add_field(name="RGB Values", value=f"```R:{r} G:{g} B:{b}```", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@guild_configured_check()
@commands.has_permissions(administrator=True)
async def welcome(ctx, *, message: str = None):
    """
    Set a custom welcome message for new tickets.
    Usage: -welcome Your custom message here
    This command can only be used by administrators.
    """
    if not message:
        await ctx.send("❌ Please provide a welcome message.\nExample: `-welcome Welcome! Please describe your issue and we'll help you soon.`")
        return

    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    config["welcome_message"] = message
    save_guild_config(guild_id, config)

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="💬 Welcome Message Updated",
        description="Custom welcome message has been set for new tickets!",
        color=embed_color
    )
    embed.add_field(name="New Message", value=f"```{message}```", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@guild_configured_check()
@commands.check(is_ticket_channel)
async def add(ctx, user: discord.Member = None):
    """
    Adds a user to the current ticket channel.
    Usage: -add @user
    This command can only be used within a ticket channel by staff or the ticket creator.
    """
    if not user:
        await ctx.send("❌ Please specify a user to add. Usage: `-add @user`")
        return

    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    tickets_data = load_guild_tickets(guild_id)

    ticket_id = None
    for tid, data in tickets_data.items():
        if data["channel_id"] == ctx.channel.id:
            ticket_id = tid
            break

    if not ticket_id:
        await ctx.send("❌ Could not find ticket information for this channel.")
        return

    ticket_info = tickets_data[ticket_id]
    is_staff = any(role.id in config["staff_role_ids"] for role in ctx.author.roles)
    is_creator = ctx.author.id == ticket_info["creator_id"]
    is_claimer = ticket_info.get("claimed_by") == ctx.author.id

    if not (is_staff or is_creator or is_claimer):
        await ctx.send("❌ You do not have permission to add users to this ticket.")
        return

    added_users = ticket_info.get("added_users", [])
    if user.id in added_users:
        await ctx.send(f"❌ {user.mention} is already added to this ticket.")
        return

    try:
        await ctx.channel.set_permissions(
            user, 
            view_channel=True, 
            send_messages=True, 
            read_messages=True, 
            attach_files=True
        )

        added_users.append(user.id)
        ticket_info["added_users"] = added_users
        tickets_data[ticket_id] = ticket_info
        save_guild_tickets(guild_id, tickets_data)

        embed_color = get_embed_color(guild_id)
        embed = discord.Embed(
            title="✅ User Added to Ticket",
            description=f"{user.mention} has been added to this ticket by {ctx.author.mention}",
            color=embed_color
        )
        await ctx.send(embed=embed)

        try:
            await user.send(f"You have been added to ticket #{ticket_id} in {ctx.guild.name}. You can access it here: {ctx.channel.mention}")
        except:
            await ctx.send(f"📧 Could not send DM to {user.mention}. They have been added to the ticket anyway.")

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to modify channel permissions.")
    except Exception as e:
        await ctx.send(f"❌ An error occurred while adding the user: {str(e)}")

@bot.command()
@guild_configured_check()
@commands.check(is_ticket_channel)
async def remove(ctx, user: discord.Member = None):
    """
    Remove a user from the current ticket channel.
    Usage: -remove @user
    This command can only be used within a ticket channel by staff or the ticket creator.
    """
    if not user:
        await ctx.send("❌ Please specify a user to remove. Usage: `-remove @user`")
        return

    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    tickets_data = load_guild_tickets(guild_id)

    ticket_id = None
    for tid, data in tickets_data.items():
        if data["channel_id"] == ctx.channel.id:
            ticket_id = tid
            break

    if not ticket_id:
        await ctx.send("❌ Could not find ticket information for this channel.")
        return

    ticket_info = tickets_data[ticket_id]
    is_staff = any(role.id in config["staff_role_ids"] for role in ctx.author.roles)
    is_creator = ctx.author.id == ticket_info["creator_id"]

    if not (is_staff or is_creator):
        await ctx.send("❌ You do not have permission to remove users from this ticket.")
        return

    # Don't allow removing the ticket creator
    if user.id == ticket_info["creator_id"]:
        await ctx.send("❌ You cannot remove the ticket creator.")
        return

    added_users = ticket_info.get("added_users", [])
    if user.id not in added_users:
        await ctx.send(f"❌ {user.mention} is not added to this ticket.")
        return

    try:
        await ctx.channel.set_permissions(user, overwrite=None)

        added_users.remove(user.id)
        ticket_info["added_users"] = added_users
        tickets_data[ticket_id] = ticket_info
        save_guild_tickets(guild_id, tickets_data)

        embed_color = get_embed_color(guild_id)
        embed = discord.Embed(
            title="🚫 User Removed from Ticket",
            description=f"{user.mention} has been removed from this ticket by {ctx.author.mention}",
            color=embed_color
        )
        await ctx.send(embed=embed)

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to modify channel permissions.")
    except Exception as e:
        await ctx.send(f"❌ An error occurred while removing the user: {str(e)}")

@bot.command()
@guild_configured_check()
@is_staff_member()
async def reopen(ctx, ticket_id: str):
    """
    Reopens a closed ticket by ID with webhook message recreation.
    Usage: -reopen 1234
    This command can only be used by staff members.
    """
    if not ticket_id:
        await ctx.send("❌ Please provide a ticket ID. Example: `-reopen 1234`")
        return

    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    tickets_data = load_guild_tickets(guild_id)

    if ticket_id not in tickets_data:
        await ctx.send(f"❌ No ticket found with ID {ticket_id}.")
        return

    ticket_info = tickets_data[ticket_id]

    if not ticket_info.get("closed", False):
        await ctx.send(f"❌ Ticket #{ticket_id} is already open.")
        return

    guild = ctx.guild
    category = guild.get_channel(config["ticket_category_id"])
    if not category:
        await ctx.send("❌ Ticket category not found. Please check the configuration.")
        return

    creator_id = ticket_info["creator_id"]
    try:
        creator = await bot.fetch_user(creator_id)
    except:
        await ctx.send("❌ Could not find the original ticket creator.")
        return

    button_name = ticket_info["button_name"]
    ticket_number = ticket_info["ticket_number"]
    new_channel_name = f"{button_name.lower()}-{ticket_number}-reopened"

    await ctx.send("🔄 Reopening ticket and recreating messages... This may take a moment.")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        creator: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True)
    }

    for role_id in config["staff_role_ids"]:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True)

    added_users = ticket_info.get("added_users", [])
    for user_id in added_users:
        user = guild.get_member(user_id)
        if user:
            overwrites[user] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True)

    new_channel = await guild.create_text_channel(
        name=new_channel_name,
        category=category,
        overwrites=overwrites
    )

    ticket_info["closed"] = False
    ticket_info["reopened"] = "Yes"
    ticket_info["channel_id"] = new_channel.id
    ticket_info["reopened_at"] = datetime.datetime.utcnow().isoformat()
    ticket_info["reopened_by"] = ctx.author.id
    tickets_data[ticket_id] = ticket_info
    save_guild_tickets(guild_id, tickets_data)

    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="__**Reopened Support Ticket**__",
        color=embed_color
    )
    embed.set_author(name=creator.display_name, icon_url=creator.avatar.url if creator.avatar else None)
    if creator.avatar:
        embed.set_thumbnail(url=creator.avatar.url)

    embed.add_field(name="__**Created by**__", value=f"```{creator.mention}```", inline=False)
    embed.add_field(name="__**Original Reason**__", value=f"```{ticket_info['reason']}```", inline=False)
    embed.add_field(name="__**Reopened by**__", value=f"```{ctx.author.mention}```", inline=False)
    embed.add_field(name="__**Priority**__", value=f"```{ticket_info.get('priority', 'Medium').title()}```", inline=False)
    embed.add_field(name="__**Ticket ID**__", value=f"```{ticket_id}```", inline=False)
    embed.set_footer(text=f"Ticket Number: {ticket_number}")

    view = TicketControlView(int(ticket_id), guild_id)
    await new_channel.send(f"🔄 This ticket has been reopened by {ctx.author.mention}.", embed=embed, view=view)

    # Recreate message history using webhooks
    log_file_path = f"logs/{guild_id}/ticket_{ticket_id}.txt"
    if os.path.exists(log_file_path):
        restore_embed = discord.Embed(
            title="📜 Recreating Previous Messages",
            description="Please wait while we restore the message history...",
            color=embed_color
        )
        status_msg = await new_channel.send(embed=restore_embed)

        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                log_content = f.read()

            # Parse messages from log file
            messages_data = []
            for line in log_content.split('\n'):
                if line.strip() and line.startswith('[') and ']: ' in line and not line.startswith('====='):
                    messages_data.append(line)

            # Recreate messages with webhook
            if messages_data:
                # Limit to last 30 messages to avoid rate limits
                recent_messages = messages_data[-30:] if len(messages_data) > 30 else messages_data

                await status_msg.edit(embed=discord.Embed(
                    title="📜 Recreating Messages",
                    description=f"Restoring {len(recent_messages)} messages... Please wait.",
                    color=embed_color
                ))

                await recreate_messages_with_webhook(new_channel, recent_messages)

                await status_msg.edit(embed=discord.Embed(
                    title="✅ Message History Restored",
                    description=f"Successfully restored {len(recent_messages)} previous messages.",
                    color=embed_color
                ))
            else:
                await status_msg.edit(embed=discord.Embed(
                    title="📜 No Message History",
                    description="No previous messages found to restore.",
                    color=embed_color
                ))

        except Exception as e:
            print(f"Error restoring message history: {e}")
            await status_msg.edit(embed=discord.Embed(
                title="⚠️ Message History Error",
                description=f"Could not restore message history: {str(e)}",
                color=embed_color
            ))
    else:
        await new_channel.send(embed=discord.Embed(
            title="📜 No Previous Messages",
            description="No message history file found for this ticket.",
            color=embed_color
        ))

    await ctx.send(f"✅ Ticket #{ticket_id} has been reopened: {new_channel.mention}", delete_after=30)

    if creator.id != ctx.author.id:
        try:
            await creator.send(f"Your ticket #{ticket_id} has been reopened by {ctx.author.mention} in {ctx.guild.name}. You can access it here: {new_channel.mention}")
        except:
            await new_channel.send(f"📧 Unable to DM {creator.mention}. Please notify them about this reopened ticket.")

@bot.command()
@guild_configured_check()
@commands.has_permissions(administrator=True)
async def toggletranscriptt(ctx):
    """
    Toggle whether transcripts are sent to users who opened tickets.
    Usage: -transcripttoggle
    This command can only be used by administrators.
    """
    guild_id = str(ctx.guild.id)
    config = load_guild_config(guild_id)
    
    current_setting = config.get("send_transcript_to_user", True)
    new_setting = not current_setting
    
    config["send_transcript_to_user"] = new_setting
    save_guild_config(guild_id, config)
    
    embed_color = get_embed_color(guild_id)
    embed = discord.Embed(
        title="📄 Transcript Setting Updated",
        description=f"Transcript sending to users is now {'**enabled**' if new_setting else '**disabled**'}",
        color=embed_color
    )
    
    if new_setting:
        embed.add_field(
            name="✅ Enabled",
            value="Users who open tickets will receive transcripts when tickets are closed or when staff generate them",
            inline=False
        )
    else:
        embed.add_field(
            name="❌ Disabled", 
            value="Transcripts will only be sent to the log channel, not to users",
            inline=False
        )
    
    embed.set_footer(text=f"Changed by {ctx.author}")
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    """Check bot latency and status"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=(
            f"**⏱️ Latency:** {latency}ms\n"
            f"**📡 Status:** Online and responsive!\n"
            f"**🏢 Guild:** {ctx.guild.name}\n"
            f"**⚙️ Configured:** {'✅ Yes' if is_guild_configured(str(ctx.guild.id)) else '❌ No'}"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(
        text=f"Requested by {ctx.author}", 
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )
    await ctx.send(embed=embed)

@bot.command()
@guild_configured_check()
async def stats(ctx):
    """Display comprehensive bot and server statistics"""
    embed = get_stats()
    embed.title = f"📊 Bot Statistics - {ctx.guild.name}"
    
    # Add guild-specific stats
    guild_id = str(ctx.guild.id)
    tickets_data = load_guild_tickets(guild_id)
    blacklist = load_guild_blacklist(guild_id)
    
    embed.add_field(
        name="🎫 Server Tickets",
        value=f"```Total: {len(tickets_data)}\nOpen: {sum(1 for t in tickets_data.values() if not t.get('closed', False))}\nClosed: {sum(1 for t in tickets_data.values() if t.get('closed', False))}```",
        inline=True
    )
    embed.add_field(
        name="🚫 Blacklisted Users",
        value=f"```{len(blacklist)}```",
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx, command_name: str = None):
    """
    Display help information for commands.
    Usage: -help [command_name]
    """
    embed_color = get_embed_color(str(ctx.guild.id)) if ctx.guild and is_guild_configured(str(ctx.guild.id)) else discord.Color.blue()

    if command_name == "setup":
        embed = discord.Embed(
            title="🔧 Setup Command Help",
            description="Configure the bot for your server",
            color=embed_color
        )
        embed.add_field(
            name="Usage",
            value="```-setup <category_id> <log_channel_id> <staff_role_id> [staff_role_id2] ...```",
            inline=False
        )
        embed.add_field(
            name="Parameters",
            value="• `category_id` - ID of the category where tickets will be created\n• `log_channel_id` - ID of the channel for ticket logs\n• `staff_role_id` - ID of staff roles that can manage tickets",
            inline=False
        )
        embed.add_field(
            name="Example",
            value="```-setup 123456789 987654321 555666777```",
            inline=False
        )
        embed.add_field(
            name="How to get IDs",
            value="1. Enable Developer Mode in Discord settings\n2. Right-click on channels/roles\n3. Select 'Copy ID'",
            inline=False
        )
    else:
        embed = discord.Embed(
            title=f"{ANIMATED_EMOJIS['ticket']} Enhanced Discord Ticket Bot - Help",
            description="A powerful multi-server Discord ticket bot with enhanced features",
            color=embed_color
        )

        if not ctx.guild or not is_guild_configured(str(ctx.guild.id)):
            embed.add_field(
                name="⚠️ Setup Required",
                value="This server needs to be configured first!\nRun `-help setup` for instructions.",
                inline=False
            )

        embed.add_field(
            name=f"{ANIMATED_EMOJIS['setting']} Setup Commands",
            value="• `-setup` - Configure bot for your server\n• `-config` - View/modify settings\n• `-panel` - Create ticket creation panel\n• `-setcolor #hex` - Set embed colors\n• `-welcome <msg>` - Set welcome message\n• `-transcripttoggle` - Toggle transcript sending to users",
            inline=False
        )

        embed.add_field(
            name=f"{ANIMATED_EMOJIS['tickets']} Ticket Management",
            value="• `-close [reason]` - Close current ticket\n• `-claim` - Claim/unclaim ticket\n• `-priority <level>` - Set priority\n• `-note add <text>` - Add staff note\n• `-note view` - View all notes\n• `-rename` - Rename ticket channel",
            inline=False
        )

        embed.add_field(
            name=f"{ANIMATED_EMOJIS['usermanage']} User Management",
            value="• `-add @user` - Add user to ticket\n• `-remove @user` - Remove user\n• `-blacklist @user` - Block from tickets\n• `-unblacklist @user` - Unblock user",
            inline=False
        )

        embed.add_field(
            name=f"{ANIMATED_EMOJIS['stats']} Statistics & Tools",
            value="• `-ticketstats` - Server statistics\n• `-reopen <id>` - Reopen closed ticket\n• `-transcript` - Generate transcript\n• `-ping` - Check bot status\n• `-help` - Show this menu",
            inline=False
        )

        embed.add_field(
            name=f"{ANIMATED_EMOJIS['sparkle']} Enhanced Features",
            value="• Auto-close after inactivity\n• Message history recreation\n• HTML transcripts\n• Priority system\n• Staff notes & tags\n• Multi-button panels",
            inline=False
        )

    embed.set_footer(text="Enhanced Multi-Server Ticket Bot v6.0 • With Webhook Recreation", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    await ctx.send(embed=embed)

# Global variables for stats
start_time = time.time()

def get_stats():
    try:
        uname = platform.uname()
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()) if psutil else datetime.datetime.now()
        os_uptime = str(datetime.datetime.now() - boot_time).split('.')[0]

        # CPU
        if psutil:
            try:
                cpu_usage = psutil.cpu_percent()
                physical_cores = psutil.cpu_count(logical=False)
                total_cores = psutil.cpu_count(logical=True)
            except:
                cpu_usage = "N/A"
                physical_cores = "N/A"
                total_cores = "N/A"
        else:
            cpu_usage = "N/A"
            physical_cores = "N/A"
            total_cores = "N/A"

        # RAM
        if psutil:
            try:
                virtual_mem = psutil.virtual_memory()
                total_ram = round(virtual_mem.total / (1024 ** 3), 2)
                used_ram = round(virtual_mem.used / (1024 ** 3), 2)
                ram_percent = virtual_mem.percent
            except:
                total_ram = used_ram = ram_percent = "N/A"
        else:
            total_ram = used_ram = ram_percent = "N/A"

        # Bot info
        python_version = platform.python_version()
        uptime_seconds = time.time() - start_time
        uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))
        bot_version = "v6.0 ENHANCED"

        # Embed
        embed = discord.Embed(
            title="🧬 Enhanced Bot Stats",
            description="```purple\nAdvanced multi-server ticket bot with enhanced features```",
            color=0x9B59B6
        )

        embed.add_field(name="📦 Bot Version", value=f"```{bot_version}```", inline=False)
        embed.add_field(name="💻 CPU", value=f"```Usage: {cpu_usage}%\nCores: {physical_cores} / {total_cores}```", inline=True)
        embed.add_field(name="💾 RAM", value=f"```{used_ram}GB / {total_ram}GB ({ram_percent}%)```", inline=True)
        embed.add_field(name="🕒 Bot Uptime", value=f"```{uptime_str}```", inline=True)
        all_members = []
        for guild in bot.guilds:
            all_members.extend(guild.members)
        try:
            all_members = []
            for guild in bot.guilds:
                all_members.extend(guild.members)
            unique_users = len(set(all_members))
        except Exception:
            unique_users = "N/A"
        embed.add_field(name="👥 Users", value=f"```{unique_users}```", inline=True)
        embed.add_field(name="🌍 Servers", value=f"```{len(bot.guilds)}```", inline=True)
        embed.add_field(name="📡 Ping", value=f"```{round(bot.latency * 1000)}ms```", inline=True)
        embed.add_field(name="🐍 Python", value=f"```{python_version}```", inline=False)

        embed.set_footer(text="Enhanced Ticket Bot v6.0 • Multi-server with Webhook Recreation")
        return embed
    except Exception as e:
        # Fallback embed if stats fail
        embed = discord.Embed(
            title="🧬 Bot Stats",
            description="```purple\nBasic bot statistics```",
            color=0x9B59B6
        )
        embed.add_field(name="📦 Bot Version", value="```v6.0 ENHANCED```", inline=False)
        embed.add_field(name="🌍 Servers", value=f"```{len(bot.guilds)}```", inline=True)
        embed.add_field(name="📡 Ping", value=f"```{round(bot.latency * 1000)}ms```", inline=True)
        embed.add_field(name="🐍 Python", value=f"```{platform.python_version()}```", inline=False)
        return embed

# ===== FUTURE FEATURE IDEAS =====
"""
🚀 ADDITIONAL FEATURES YOU COULD ADD:

1. 📊 ADVANCED ANALYTICS:
   - Response time tracking for staff
   - Customer satisfaction ratings
   - Weekly/monthly ticket reports
   - Peak hours analysis

2. 🔄 TICKET TEMPLATES:
   - Pre-defined response templates
   - Auto-suggest responses based on keywords
   - FAQ integration

3. 🎯 SMART ROUTING:
   - Auto-assign tickets based on staff expertise
   - Queue system for high-priority tickets
   - Load balancing between staff members

4. 📱 NOTIFICATIONS:
   - Email notifications for ticket updates
   - Mobile push notifications
   - Slack/Teams integration for staff alerts

5. 🔍 SEARCH & FILTERING:
   - Search tickets by content, user, or date
   - Advanced filtering options
   - Archive management

6. 🎨 CUSTOMIZATION:
   - Custom embed designs per category
   - Themed ticket panels
   - Brand colors and logos

7. 🔒 SECURITY FEATURES:
   - Ticket encryption for sensitive data
   - Staff permission levels
   - Audit logs for all actions

8. 🤖 AI INTEGRATION:
   - Auto-categorization of tickets
   - Sentiment analysis
   - Suggested responses using OpenAI

9. 📋 FORMS & SURVEYS:
   - Custom intake forms
   - Post-resolution surveys
   - Multi-step ticket creation

10. 🔗 INTEGRATIONS:
    - CRM system integration
    - Database connectivity
    - External API webhooks
    - Payment processing for premium support

Would you like me to implement any of these features?
"""

# Run the bot
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN environment variable not set!")
        print("Please set your Discord bot token in the Secrets tab.")
        exit(1)
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ ERROR: Failed to start bot: {e}")
        exit(1)❌ ERROR: Failed to start bot: {e}")
        exit(1)