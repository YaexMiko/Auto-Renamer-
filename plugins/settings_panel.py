import asyncio
import math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, InputMediaPhoto
from helper.database import DARKXSIDE78
from config import Config
import logging

# Store user states with message context for proper redirection
user_states = {}

# Store original settings message references
settings_messages = {}

SETTINGS_PHOTO = "https://graph.org/file/a27d85469761da836337c.jpg"

async def get_settings_photo(user_id: int):
    """Get the photo to use for settings panel - user's thumbnail if exists, else default"""
    user_thumbnail = await DARKXSIDE78.get_thumbnail(user_id)
    if user_thumbnail:
        return user_thumbnail
    else:
        return SETTINGS_PHOTO

def get_readable_file_size(size_bytes):
    """Convert bytes to readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

@Client.on_message(filters.private & filters.command("settings"))
async def settings_command(client, message: Message):
    """Main settings command"""
    user_id = message.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Get current metadata status
    metadata_status = await DARKXSIDE78.get_metadata(user_id)
    
    # Get current thumbnail status - check if file_id exists
    thumbnail_status = await DARKXSIDE78.get_thumbnail(user_id)
    
    # Create settings overview text
    auto_rename_status = 'Disabled (Manual Mode)' if settings['rename_mode'] == 'Manual' else 'Enabled'
    
    settings_text = f"""**🛠️ Settings for** `{message.from_user.first_name}` **⚙️**

**Custom Thumbnail:** {'Exists' if thumbnail_status else 'Not Exists'}
**Upload Type:** {settings['send_as'].upper()}
**Prefix:** {settings['prefix'] or 'None'}
**Suffix:** {settings['suffix'] or 'None'}

**Upload Destination:** {settings['upload_destination'] or 'None'}
**Sample Video:** {'Enabled' if settings['sample_video'] else 'Disabled'}
**Screenshot:** {'Enabled' if settings['screenshot_enabled'] else 'Disabled'}

**Metadata:** {'Enabled' if metadata_status != 'Off' else 'Disabled'}
**Remove/Replace Words:** {settings['remove_words'] or 'None'}
**Rename mode:** {settings['rename_mode']}
**Auto-Rename:** {auto_rename_status}"""

    # Create main settings keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Choose Format", callback_data="setting_send_as"),
            InlineKeyboardButton("Set Upload Destination", callback_data="setting_upload_dest")
        ],
        [
            InlineKeyboardButton("Set Thumbnail", callback_data="setting_thumbnail"),
            InlineKeyboardButton("Set Caption", callback_data="setting_caption")
        ],
        [
            InlineKeyboardButton("Set Prefix", callback_data="setting_prefix"),
            InlineKeyboardButton("Set Suffix", callback_data="setting_suffix")
        ],
        [
            InlineKeyboardButton(f"Rename Mode | {settings['rename_mode']}", callback_data="setting_rename_mode"),
            InlineKeyboardButton("Set Metadata", callback_data="setting_metadata")
        ],
        [
            InlineKeyboardButton("Remove Words", callback_data="setting_remove_words"),
            InlineKeyboardButton(f"Enable Sample Video", callback_data="setting_sample_video")
        ],
        [
            InlineKeyboardButton(f"Enable Screenshot", callback_data="setting_screenshot")
        ]
    ])

    # Get the appropriate photo - user's thumbnail or default
    settings_photo = await get_settings_photo(user_id)

    try:
        sent_msg = await message.reply_photo(
            photo=settings_photo,
            caption=settings_text,
            reply_markup=keyboard
        )
        # Store the settings message reference
        settings_messages[user_id] = sent_msg
    except Exception as e:
        sent_msg = await message.reply_text(settings_text, reply_markup=keyboard)
        settings_messages[user_id] = sent_msg

@Client.on_callback_query(filters.regex(r"^setting_"))
async def settings_callback_handler(client, query: CallbackQuery):
    """Handle all settings callbacks"""
    user_id = query.from_user.id
    data = query.data
    
    try:
        if data == "setting_close":
            await query.message.delete()
            if user_id in settings_messages:
                del settings_messages[user_id]
            if user_id in user_states:
                del user_states[user_id]
            return
            
        elif data == "setting_send_as":
            await handle_send_as(client, query)
            
        elif data == "setting_upload_dest":
            await handle_upload_destination(client, query)
            
        elif data == "setting_thumbnail":
            await handle_thumbnail_setting(client, query)
            
        elif data == "setting_caption":
            await handle_caption_setting(client, query)
            
        elif data == "setting_prefix":
            await handle_prefix_setting(client, query)
            
        elif data == "setting_suffix":
            await handle_suffix_setting(client, query)
            
        elif data == "setting_rename_mode":
            await handle_rename_mode(client, query)
            
        elif data == "setting_metadata":
            # Clear any user states when going to metadata
            if user_id in user_states:
                del user_states[user_id]
            
            # Import and show metadata
            try:
                from plugins.metadata import metadata
                await metadata(client, query.message)
            except ImportError:
                await query.answer("Metadata module not found", show_alert=True)
            
        elif data == "setting_remove_words":
            await handle_remove_words_setting(client, query)
            
        elif data == "setting_sample_video":
            await handle_sample_video_setting(client, query)
            
        elif data == "setting_screenshot":
            await handle_screenshot_setting(client, query)
            
        # Handle back to main settings
        elif data == "settings_back":
            await show_main_settings(client, query)
            
        # Handle send_as selections
        elif data.startswith("sendas_"):
            await handle_send_as_selection(client, query)
            
        # Handle rename mode selections
        elif data.startswith("rename_mode_"):
            await handle_rename_mode_selection(client, query)
            
    except Exception as e:
        logging.error(f"Settings callback error: {e}")
        await query.answer("An error occurred", show_alert=True)

async def show_main_settings(client, query: CallbackQuery):
    """Show main settings panel"""
    user_id = query.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Get current metadata status
    metadata_status = await DARKXSIDE78.get_metadata(user_id)
    
    # Get current thumbnail status
    thumbnail_status = await DARKXSIDE78.get_thumbnail(user_id)
    
    # Create settings overview text
    auto_rename_status = 'Disabled (Manual Mode)' if settings['rename_mode'] == 'Manual' else 'Enabled'
    
    settings_text = f"""**🛠️ Settings for** `{query.from_user.first_name}` **⚙️**

**Custom Thumbnail:** {'Exists' if thumbnail_status else 'Not Exists'}
**Upload Type:** {settings['send_as'].upper()}
**Prefix:** {settings['prefix'] or 'None'}
**Suffix:** {settings['suffix'] or 'None'}

**Upload Destination:** {settings['upload_destination'] or 'None'}
**Sample Video:** {'Enabled' if settings['sample_video'] else 'Disabled'}
**Screenshot:** {'Enabled' if settings['screenshot_enabled'] else 'Disabled'}

**Metadata:** {'Enabled' if metadata_status != 'Off' else 'Disabled'}
**Remove/Replace Words:** {settings['remove_words'] or 'None'}
**Rename mode:** {settings['rename_mode']}
**Auto-Rename:** {auto_rename_status}"""

    # Create main settings keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Choose Format", callback_data="setting_send_as"),
            InlineKeyboardButton("Set Upload Destination", callback_data="setting_upload_dest")
        ],
        [
            InlineKeyboardButton("Set Thumbnail", callback_data="setting_thumbnail"),
            InlineKeyboardButton("Set Caption", callback_data="setting_caption")
        ],
        [
            InlineKeyboardButton("Set Prefix", callback_data="setting_prefix"),
            InlineKeyboardButton("Set Suffix", callback_data="setting_suffix")
        ],
        [
            InlineKeyboardButton(f"Rename Mode | {settings['rename_mode']}", callback_data="setting_rename_mode"),
            InlineKeyboardButton("Set Metadata", callback_data="setting_metadata")
        ],
        [
            InlineKeyboardButton("Remove Words", callback_data="setting_remove_words"),
            InlineKeyboardButton(f"Enable Sample Video", callback_data="setting_sample_video")
        ],
        [
            InlineKeyboardButton(f"Enable Screenshot", callback_data="setting_screenshot")
        ]
    ])

    try:
        await query.message.edit_caption(
            caption=settings_text,
            reply_markup=keyboard
        )
    except:
        await query.message.edit_text(
            text=settings_text,
            reply_markup=keyboard
        )

async def handle_send_as(client, query: CallbackQuery):
    """Handle send as setting"""
    user_id = query.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    text = f"""**📤 Choose Upload Format**

Current: **{settings.get('send_as', 'DOCUMENT').upper()}**

Select how you want files to be uploaded:"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Document{'✅' if settings.get('send_as') == 'DOCUMENT' else ''}", callback_data="sendas_document"),
            InlineKeyboardButton(f"Media{'✅' if settings.get('send_as') == 'media' else ''}", callback_data="sendas_media")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
    ])
    
    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard)
    except:
        await query.message.edit_text(text=text, reply_markup=keyboard)

async def handle_send_as_selection(client, query: CallbackQuery):
    """Handle send as selection"""
    user_id = query.from_user.id
    
    if query.data == "sendas_document":
        await DARKXSIDE78.update_user_setting(user_id, 'send_as', 'DOCUMENT')
        await query.answer("Upload format set to Document ✅")
    elif query.data == "sendas_media":
        await DARKXSIDE78.update_user_setting(user_id, 'send_as', 'media')
        await query.answer("Upload format set to Media ✅")
    
    # Go back to main settings
    await show_main_settings(client, query)

async def handle_rename_mode(client, query: CallbackQuery):
    """Handle rename mode setting"""
    user_id = query.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    text = f"""**🔄 Choose Rename Mode**

Current: **{settings.get('rename_mode', 'Manual')}**

**Manual**: You manually enter new filename for each file
**Auto**: Files are automatically renamed using prefix/suffix settings"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"Manual{'✅' if settings.get('rename_mode') == 'Manual' else ''}", callback_data="rename_mode_manual"),
            InlineKeyboardButton(f"Auto{'✅' if settings.get('rename_mode') == 'Auto' else ''}", callback_data="rename_mode_auto")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
    ])
    
    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard)
    except:
        await query.message.edit_text(text=text, reply_markup=keyboard)

async def handle_rename_mode_selection(client, query: CallbackQuery):
    """Handle rename mode selection"""
    user_id = query.from_user.id
    
    if query.data == "rename_mode_manual":
        await DARKXSIDE78.update_user_setting(user_id, 'rename_mode', 'Manual')
        await DARKXSIDE78.update_user_setting(user_id, 'manual_mode', True)
        await query.answer("Rename mode set to Manual ✅")
    elif query.data == "rename_mode_auto":
        await DARKXSIDE78.update_user_setting(user_id, 'rename_mode', 'Auto')
        await DARKXSIDE78.update_user_setting(user_id, 'manual_mode', False)
        await query.answer("Rename mode set to Auto ✅")
    
    # Go back to main settings
    await show_main_settings(client, query)

async def handle_upload_destination(client, query: CallbackQuery):
    """Handle upload destination setting"""
    await query.answer("This feature will be available soon!", show_alert=True)

async def handle_thumbnail_setting(client, query: CallbackQuery):
    """Handle thumbnail setting"""
    text = """**🖼️ Set Custom Thumbnail**

Send a photo to set as your custom thumbnail for all uploads.

Current thumbnail will be shown in settings."""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
    ])
    
    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard)
    except:
        await query.message.edit_text(text=text, reply_markup=keyboard)

async def handle_caption_setting(client, query: CallbackQuery):
    """Handle caption setting"""
    user_id = query.from_user.id
    caption = await DARKXSIDE78.get_caption(user_id)
    
    text = f"""**📝 Set Custom Caption**

Current Caption: {caption or 'None'}

Use /set_caption <text> to set custom caption
Use /del_caption to remove caption
Use /see_caption to view current caption"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
    ])
    
    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard)
    except:
        await query.message.edit_text(text=text, reply_markup=keyboard)

async def handle_prefix_setting(client, query: CallbackQuery):
    """Handle prefix setting"""
    user_id = query.from_user.id
    
    # Set user state for prefix input
    user_states[user_id] = {
        'action': 'set_prefix',
        'message': query.message
    }
    
    prefix = await DARKXSIDE78.get_prefix(user_id)
    
    text = f"""**📝 Set Prefix**

Current Prefix: `{prefix or 'None'}`

Send the prefix you want to add before filename.
Send /cancel to cancel."""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
    ])
    
    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard)
    except:
        await query.message.edit_text(text=text, reply_markup=keyboard)

async def handle_suffix_setting(client, query: CallbackQuery):
    """Handle suffix setting"""
    user_id = query.from_user.id
    
    # Set user state for suffix input
    user_states[user_id] = {
        'action': 'set_suffix',
        'message': query.message
    }
    
    suffix = await DARKXSIDE78.get_suffix(user_id)
    
    text = f"""**📝 Set Suffix**

Current Suffix: `{suffix or 'None'}`

Send the suffix you want to add after filename.
Send /cancel to cancel."""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
    ])
    
    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard)
    except:
        await query.message.edit_text(text=text, reply_markup=keyboard)

async def handle_remove_words_setting(client, query: CallbackQuery):
    """Handle remove words setting"""
    user_id = query.from_user.id
    
    # Set user state for remove words input
    user_states[user_id] = {
        'action': 'set_remove_words',
        'message': query.message
    }
    
    remove_words = await DARKXSIDE78.get_remove_words(user_id)
    
    text = f"""**🗑️ Set Remove Words**

Current Remove Words: `{remove_words or 'None'}`

Send words to remove from filename (separated by commas).
Example: word1,word2,word3

Send /cancel to cancel."""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
    ])
    
    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard)
    except:
        await query.message.edit_text(text=text, reply_markup=keyboard)

async def handle_sample_video_setting(client, query: CallbackQuery):
    """Handle sample video setting"""
    user_id = query.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Toggle sample video setting
    new_value = not settings.get('sample_video', False)
    await DARKXSIDE78.update_user_setting(user_id, 'sample_video', new_value)
    
    status = "Enabled" if new_value else "Disabled"
    await query.answer(f"Sample Video {status} ✅")
    
    # Go back to main settings
    await show_main_settings(client, query)

async def handle_screenshot_setting(client, query: CallbackQuery):
    """Handle screenshot setting"""
    user_id = query.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Toggle screenshot setting
    new_value = not settings.get('screenshot_enabled', False)
    await DARKXSIDE78.update_user_setting(user_id, 'screenshot_enabled', new_value)
    
    status = "Enabled" if new_value else "Disabled"
    await query.answer(f"Screenshot {status} ✅")
    
    # Go back to main settings
    await show_main_settings(client, query)

# Handle text input for settings
@Client.on_message(filters.private & filters.text & ~filters.command(['start', 'help', 'settings', 'cancel']))
async def handle_settings_text_input(client, message: Message):
    """Handle text input for settings"""
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    user_state = user_states[user_id]
    action = user_state.get('action')
    
    if not action:
        return
    
    text_input = message.text.strip()
    
    try:
        # Delete user's input message
        await message.delete()
    except:
        pass
    
    try:
        if action == 'set_prefix':
            await DARKXSIDE78.set_prefix(user_id, text_input)
            await client.send_message(user_id, f"✅ Prefix set to: `{text_input}`")
            
        elif action == 'set_suffix':
            await DARKXSIDE78.set_suffix(user_id, text_input)
            await client.send_message(user_id, f"✅ Suffix set to: `{text_input}`")
            
        elif action == 'set_remove_words':
            await DARKXSIDE78.set_remove_words(user_id, text_input)
            await client.send_message(user_id, f"✅ Remove words set to: `{text_input}`")
        
        # Clear user state
        del user_states[user_id]
        
        # Show updated settings after a delay
        await asyncio.sleep(2)
        
        # Get the original settings message
        if user_id in settings_messages:
            original_msg = settings_messages[user_id]
            # Create a fake query object to reuse the show_main_settings function
            class FakeQuery:
                def __init__(self, message, from_user):
                    self.message = message
                    self.from_user = from_user
            
            fake_query = FakeQuery(original_msg, message.from_user)
            await show_main_settings(client, fake_query)
        
    except Exception as e:
        logging.error(f"Error handling settings input: {e}")
        if user_id in user_states:
            del user_states[user_id]

@Client.on_message(filters.private & filters.command('cancel'))
async def cancel_settings_input(client, message: Message):
    """Cancel settings input"""
    user_id = message.from_user.id
    
    if user_id in user_states:
        del user_states[user_id]
        await message.reply_text("❌ **Cancelled**")
    else:
        await message.reply_text("Nothing to cancel.")
