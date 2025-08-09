<!-- PROJECT HEADER -->
<div align="center">
  <h1>🎫 Enhanced Multi-Server Discord Ticket Bot</h1>
  <p>
    <em>Powerful, customizable ticket management bot for Discord with advanced features, built on discord.py</em>
  </p>

  <!-- Badges -->
  <p>
    <img src="https://img.shields.io/github/license/brucewayne34/discord-ticket-bot?style=for-the-badge" alt="License">
    <img src="https://img.shields.io/github/stars/brucewayne34/discord-ticket-bot?style=for-the-badge" alt="Stars">
    <img src="https://img.shields.io/github/forks/brucewayne34/discord-ticket-bot?style=for-the-badge" alt="Forks">
    <img src="https://img.shields.io/github/issues/brucewayne34/discord-ticket-bot?style=for-the-badge" alt="Issues">
    <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python" alt="Python">
  </p>

  <img src="https://iili.io/FLKE4IV.md.jpg" alt="Bot Preview" width="80%">
</div>

---

## ✨ Features
- ⚡ **Multi-Server Support** — Each guild has isolated settings.
- 🎯 **Interactive Panels** — Ticket buttons with customizable labels.
- 📝 **Modal Ticket Creation** — Users submit issues with forms.
- 🛡 **Blacklist & Permissions** — Control who can create or manage tickets.
- 📂 **Automatic Transcripts** — HTML + TXT formats with Discord styling.
- 🖥 **Webhook Message Recreation** — Preserve original avatars & usernames.
- 🎨 **Custom Embed Colors** — Match your server branding.
- 🚀 **Optimized Performance** — Rate limiting to prevent spam.

---

## 📸 Screenshots
<details>
<summary>Click to view</summary>

![Ticket Panel]([https://i.imgur.com/XyZ1234.png](https://ddg21s9t062h4.cloudfront.net/0adqj%2Fpreview%2F69784894%2Fmain_large.jpg?response-content-disposition=inline%3Bfilename%3D%22main_large.jpg%22%3B&response-content-type=image%2Fjpeg&Expires=1754728111&Signature=gw5F-maXNndZcx~oVDQiqp46QhjEvjsTz0Rnwfc7nl9mkF6Y2BSr3kGA~KrDrqyilH2hEZrwVLC3OnOQUn9meOWkydx~weVwn-uOA1XoFK9pdlPwkmxOLOGU~entSJdgt2X6yWA7b42IgEA2HA38LpH6cGxDR2zLx7nds6qzhRGGttZ9cWNcg7pUQkwprlm9NKTdDsid0xKexqLsSxSoZP7F-szzAoLrgqfFORqPOTK~zWcspCsxTXJx0vFI7xNoooWKXGgl6JJUxG9VRYu-ETOHHubbxpA3hxBlDgCsa7EYK~MLxrz~HMBzrKafwuMNGJecQyAEUBwIVXdhJth3mQ__&Key-Pair-Id=APKAJT5WQLLEOADKLHBQ))
![Transcript Example]([https://i.imgur.com/ABc5678.png](https://d3rshtj5w2m4qx.cloudfront.net/7sdqj%2Fpreview%2F69784912%2Fmain_large.jpg?response-content-disposition=inline%3Bfilename%3D%22main_large.jpg%22%3B&response-content-type=image%2Fjpeg&Expires=1754728232&Signature=gi5b5aYPb-RfDM~ih5W14v7vcl9MW3D2r2EllSN2DDSWam0dZ83RsQ-3ldjIJsOId-vEvwcler23Sb9YDvS7EUgZFQecDvsNhUl20iWnPI8WLBIT8P7bKhiadqGhcPjabDPHCI4Zxgo1uzk0Cj4vPJgE~CN4dkXtkmR5BOqiY1~TD5Q5Ga~mvB94ZdjClwJjuIBuglXeYkx2xWGwMlUfLWfi8sDBEcqQOsHLwT7ZIl9L~1R0g0SPTQAqmiQmNaDUnMz5nuzClDb2Y5y9nNlIJGyQTCKXgDzBwrdt0zCiUNI37RUp~gcTTjS0fCcHmHrCcevgwxR8u0YAUXGU2j7vpA__&Key-Pair-Id=APKAJT5WQLLEOADKLHBQ))


</details>

## 📦 Installation```

```bash
git clone https://github.com/brucewayne34/discord-ticket-bot.git
cd discord-ticket-bot
pip install -r requirements.txt
```
⚙️ Configuration

📁 Config File (configs/{guild_id}.json)
```
{
    "embed_color": [128, 0, 255],
    "ticket_category_id": 123456789012345678,
    "log_channel_id": 123456789012345678,
    "staff_role_ids": [123456789012345678],
    "max_tickets_per_user": 3,
    "welcome_message": "Welcome to your ticket!",
    "send_transcript_to_user": true
}
```
📁 Directory structure 

```
configs/     → Per-server bot settings
tickets/        → Ticket data for each guild
blacklists/     → List of blacklisted users
warnings/       → Issued warnings
tags/           → Custom server tags
panels/         → Ticket panel layouts
transcripts/    → Generated ticket transcripts
logs/           → Ticket closure logs

```
📄 Commands

Command 	 Description

-setup	   Configure the bot for the server
-panel	    Create a ticket panel
-blacklist	Add/remove users from blacklist
-warn	      Warn a user
-tag	      Manage tags



---

📜 Transcripts

HTML format — Discord-style with avatars, embeds, attachments

TXT format — Mobile-friendly plain text version

Saved in /transcripts/{guild_id}/



---

🛠 Tech Stack

Python 3.8+

discord.py

aiohttp

psutil (optional)



---

📌 Roadmap

[ ] Web Dashboard

[ ] Slash Command Support

[ ] Database Storage (MongoDB/PostgreSQL)



---

🔒 Security

⚠ Important:

Store bot tokens in .env or environment variables

Never commit configs/ or tickets/ folders to GitHub



---

📄 License

Distributed under the MIT License. See LICENSE for details.
