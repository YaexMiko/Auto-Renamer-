import os
from os import environ 

class Config:
    # Bot Configuration - Handle swapped credentials
    API_ID_ENV = environ.get("API_ID", "28614709")
    API_HASH_ENV = environ.get("API_HASH", "f36fd2ee6e3d3a17c4d244ff6dc1bac8")
    
    # Fix swapped credentials: API_ID should be numeric, API_HASH should be string
    if API_ID_ENV.isdigit():
        API_ID = int(API_ID_ENV)
        API_HASH = API_HASH_ENV
    elif API_HASH_ENV.isdigit():
        # Values are swapped
        API_ID = int(API_HASH_ENV)
        API_HASH = API_ID_ENV
    else:
        API_ID = 0
        API_HASH = ""
    
    BOT_TOKEN = environ.get("BOT_TOKEN", "7512154282:AAFGm5R7s_9iCDRmlj5VrFSkJheimWV-rZM")
    BOT_USERNAME = environ.get("BOT_USERNAME", "Tesfyrdcboybot")
    
    # Admin Configuration
    ADMIN = list(map(int, environ.get("ADMIN", "7970350353").split()))
    ADMINS = ADMIN  # For compatibility with uploaded files
    
    # Database Configuration
    DB_URL = environ.get("DB_URL", "mongodb+srv://ZeroTwo:aloksingh@zerotwo.3q3ij.mongodb.net/?retryWrites=true&w=majority")
    DB_NAME = environ.get("DB_NAME", "AutoRenameBot")
    
    # Channels Configuration
    FORCE_SUB_CHANNELS = environ.get("FORCE_SUB_CHANNELS", "").split(",") if environ.get("FORCE_SUB_CHANNELS") else []
    LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "0")) if environ.get("LOG_CHANNEL") else None
    
    # Media Configuration
    START_PIC = environ.get("START_PIC", "https://graph.org/file/a27d85469761da836337c.jpg")
    SETTINGS_PHOTO = environ.get("SETTINGS_PHOTO", "https://graph.org/file/a27d85469761da836337c.jpg")
    
    # Server Configuration
    WEBHOOK = environ.get("WEBHOOK", "True").lower() == "true"
    BOT_UPTIME = environ.get("BOT_UPTIME", "")
    
    # Token System Configuration
    TOKEN_ID_LENGTH = 8
    SHORTENER_API = environ.get("SHORTENER_API", "")
    SHORTENER_URL = environ.get("SHORTENER_URL", "")
    
    # File Processing Configuration
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    DOWNLOAD_LOCATION = "./downloads/"
    
    # Anti-NSFW Configuration
    ANTI_NSFW_ENABLED = environ.get("ANTI_NSFW_ENABLED", "True").lower() == "true"

class Txt:
    START_TXT = """
**ʜᴇʟʟᴏ {} 👋**

**ɪ ᴀᴍ ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ʙᴏᴛ ᴡɪᴛʜ ᴍᴀɴʏ ғᴇᴀᴛᴜʀᴇs**

**I can rename your files with custom templates!**

**Use /settings to configure rename options**
"""

    ABOUT_TXT = """
╭───────────⍟
├🤖 **ᴍy ɴᴀᴍᴇ:** [ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ](https://t.me/AutoRenameBot)
├🖥️ **ꜱᴇʀᴠᴇʀ:** Heroku
├📕 **ʟɪʙʀᴀʀy:** Pyrogram
├✏️ **ʟᴀɴɢᴜᴀɢᴇ:** Python 3
├📂 **ᴅᴀᴛᴀʙᴀꜱᴇ:** MongoDB
├📊 **ʙᴏᴛ ᴠᴇʀꜱɪᴏɴ:** v2.7.8
├🌟 **ᴀᴜᴛʜᴏʀ:** [DARKXSIDE78](https://t.me/DARKXSIDE78)
╰───────────⍟
"""

    HELP_TXT = """
**🔸 Available Commands:**

**📝 Basic Commands:**
• `/start` - Start the bot
• `/autorename <template>` - Set auto rename format
• `/setmedia` - Choose media type preference
• `/settings` - Open comprehensive settings panel
• `/help` - Show this help message

**🎯 File Management:**
• `/ssequence` - Start file sequence
• `/esequence` - End file sequence
• Send photo to set thumbnail
• `/viewthumb` - View current thumbnail
• `/delthumb` - Delete thumbnail

**⚙️ Settings:**
• `/metadata` - Configure metadata settings
• `/set_caption <text>` - Set custom caption
• `/see_caption` - View current caption
• `/del_caption` - Delete caption

**💎 Token System:**
• `/token` - Check token balance
• `/gentoken` - Generate token link

**📊 Admin Commands:**
• `/add_token <amount> <user>` - Add tokens
• `/remove_token <amount> <user>` - Remove tokens
• `/add_premium <user> <duration>` - Add premium
• `/remove_premium <user>` - Remove premium
• `/broadcast <message>` - Broadcast message
• `/status` - Bot statistics
"""

    META_TXT = """
**🔧 How to Set Metadata:**

**Use these commands to set metadata:**

• `/settitle <title>` - Set video title
• `/setauthor <author>` - Set author name
• `/setartist <artist>` - Set artist name
• `/setaudio <audio>` - Set audio title
• `/setsubtitle <subtitle>` - Set subtitle
• `/setvideo <video>` - Set video title
• `/setencoded_by <name>` - Set encoder name
• `/setcustom_tag <tag>` - Set custom tag

**Example:**
`/settitle My Video Title`
`/setauthor @MyChannel`

**Note:** Metadata will be added to all processed files when enabled.
"""

    PREMIUM_TXT = """
**💎 Premium Features:**

**🌟 Benefits:**
• Unlimited file renaming
• No token consumption
• Priority processing
• Faster upload/download speeds
• Advanced features access

**🎯 How to Get Premium:**
• Contact admin for premium access
• Monthly/Yearly subscriptions available
• Special discounts for bulk purchases

**💬 Contact:** @Bots_Nations_Support
"""

    FILE_NAME_TXT = """
**📝 Auto Rename Tutorial:**

**Available Variables:**
• `episode` or `Episode` or `EPISODE` - Episode number
• `quality` or `Quality` or `QUALITY` - Video quality

**Example Format:**
`Naruto Episode [episode] [quality]`

**Current Template:** `{format_template}`

**How to Use:**
1. Set format using `/autorename <template>`
2. Send files to be renamed automatically
3. Bot will detect episode and quality from filename

**Note:** Template will be applied to all files you send!
"""

    PROGRESS_BAR = """\n
╭──⌯────────────────────╮
│ 🔄 **ᴘʀᴏɢʀᴇss :** {0}%
│ 📊 **ᴘʀᴏᴄᴇssᴇᴅ :** {1}
│ 📁 **ᴛᴏᴛᴀʟ sɪᴢᴇ :** {2}
│ 🚀 **sᴘᴇᴇᴅ :** {3}/s
│ ⏱️ **ᴇᴛᴀ :** {4}
╰─────────────────⌯─────╯ """
