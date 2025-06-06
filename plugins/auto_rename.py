import asyncio
import logging
import math
import os
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import DARKXSIDE78

def get_readable_file_size(size_bytes):
    """Convert bytes to readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message: Message):
    """Auto rename command handler"""
    user_id = message.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Check if Manual Mode is active
    if settings.get('rename_mode') == "Manual":
        await message.reply_text(
            "❌ **Auto-rename disabled**\n\n"
            "Manual Mode is currently active. Auto-rename functionality is disabled.\n\n"
            "To enable auto-rename:\n"
            "• Go to Settings → Rename Mode\n"
            "• Select 'Auto' mode"
        )
        return
    
    # Show auto rename options
    text = f"""**🔄 Auto Rename Configuration**

Current Mode: **{settings.get('rename_mode', 'Manual')}**

Choose auto rename options:"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Quick Auto Rename", callback_data="autorename_quick")],
        [InlineKeyboardButton("⚙️ Configure Settings", callback_data="autorename_settings")],
        [InlineKeyboardButton("❌ Close", callback_data="autorename_close")]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^autorename_"))
async def auto_rename_callbacks(client, query):
    """Handle auto rename callbacks"""
    data = query.data
    user_id = query.from_user.id
    
    if data == "autorename_close":
        await query.message.delete()
        
    elif data == "autorename_quick":
        # Set Auto mode
        await DARKXSIDE78.update_user_setting(user_id, 'rename_mode', 'Auto')
        await query.answer("Quick Auto Rename Mode Enabled ✅")
        await query.message.edit_text(
            "✅ **Quick Auto Rename Enabled**\n\n"
            "Now send any file and it will be automatically renamed using your template!"
        )
        
    elif data == "autorename_settings":
        # Redirect to settings
        try:
            from plugins.settings_panel import show_main_settings
            await show_main_settings(client, query)
        except ImportError:
            await query.answer("Settings not available", show_alert=True)

async def auto_rename_file(client, message: Message):
    """Auto rename file - only if not in Manual mode"""
    user_id = message.from_user.id
    settings = await DARKXSIDE78.get_user_settings(user_id)
    
    # Check if Manual Mode is active
    if settings.get('rename_mode') == "Manual":
        return False
    
    rename_mode = settings.get('rename_mode', 'Manual')
    
    if rename_mode == "Auto":
        return await handle_auto_rename(client, message)
    
    return False

async def handle_auto_rename(client, message: Message):
    """Handle automatic renaming using patterns"""
    try:
        user_id = message.from_user.id
        
        # Get file info
        file_name = None
        if message.document:
            file_name = message.document.file_name
        elif message.video:
            file_name = message.video.file_name
        elif message.audio:
            file_name = message.audio.file_name
        
        if not file_name:
            return False
        
        # Get user settings
        prefix = await DARKXSIDE78.get_prefix(user_id) or ""
        suffix = await DARKXSIDE78.get_suffix(user_id) or ""
        remove_words = await DARKXSIDE78.get_remove_words(user_id) or ""
        
        # Process filename
        new_name = process_filename_auto(file_name, prefix, suffix, remove_words)
        
        if new_name != file_name:
            # Show auto rename result
            text = f"""**🔄 Auto Rename Applied**

**Original:** `{file_name}`
**Renamed:** `{new_name}`

Processing file..."""
            
            status_msg = await message.reply_text(text)
            
            # Apply the rename and upload
            success = await rename_and_upload_file(client, message, new_name)
            
            if success:
                await status_msg.edit_text(
                    f"✅ **File Auto Renamed & Uploaded**\n\n"
                    f"**New Name:** `{new_name}`"
                )
            else:
                await status_msg.edit_text("❌ **Auto Rename Failed**")
                
            return success
        
        return False
        
    except Exception as e:
        logging.error(f"Auto rename error: {e}")
        return False

def process_filename_auto(filename, prefix="", suffix="", remove_words=""):
    """Process filename with auto rename settings"""
    try:
        # Remove unwanted words
        if remove_words:
            words_to_remove = [word.strip() for word in remove_words.split(',')]
            for word in words_to_remove:
                if word:
                    filename = filename.replace(word, "")
        
        # Clean up multiple spaces and dots
        filename = re.sub(r'\.+', '.', filename)
        filename = re.sub(r'\s+', ' ', filename)
        filename = filename.strip()
        
        # Split filename and extension
        name, ext = os.path.splitext(filename)
        
        # Add prefix and suffix
        if prefix:
            name = f"{prefix} {name}"
        if suffix:
            name = f"{name} {suffix}"
        
        # Clean up again
        name = name.strip()
        
        return f"{name}{ext}"
        
    except Exception as e:
        logging.error(f"Error processing filename: {e}")
        return filename

async def rename_and_upload_file(client, message: Message, new_filename):
    """Rename and upload file with progress tracking"""
    try:
        user_id = message.from_user.id
        
        # Show downloading status
        progress_msg = await message.reply_text("📥 **Downloading file...**")
        
        # Download file
        file_path = await message.download()
        
        # Update status
        await progress_msg.edit_text("🔄 **Renaming file...**")
        
        # Create new file path with new name
        directory = os.path.dirname(file_path)
        new_file_path = os.path.join(directory, new_filename)
        
        # Rename file
        os.rename(file_path, new_file_path)
        
        # Update status
        await progress_msg.edit_text("📤 **Uploading file...**")
        
        # Get user settings for upload
        settings = await DARKXSIDE78.get_user_settings(user_id)
        thumbnail = await DARKXSIDE78.get_thumbnail(user_id)
        caption = await DARKXSIDE78.get_caption(user_id)
        
        # Prepare caption
        final_caption = caption or new_filename
        
        # Upload based on file type and settings
        if message.document:
            if settings.get('send_as') == 'media' and new_filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
                await client.send_video(
                    chat_id=message.chat.id,
                    video=new_file_path,
                    caption=final_caption,
                    thumb=thumbnail,
                    supports_streaming=True
                )
            else:
                await client.send_document(
                    chat_id=message.chat.id,
                    document=new_file_path,
                    caption=final_caption,
                    thumb=thumbnail
                )
        elif message.video:
            await client.send_video(
                chat_id=message.chat.id,
                video=new_file_path,
                caption=final_caption,
                thumb=thumbnail,
                supports_streaming=True
            )
        elif message.audio:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=new_file_path,
                caption=final_caption,
                thumb=thumbnail
            )
        
        # Clean up
        try:
            os.remove(new_file_path)
        except:
            pass
        
        # Delete progress message
        try:
            await progress_msg.delete()
        except:
            pass
        
        return True
        
    except Exception as e:
        logging.error(f"Error in rename and upload: {e}")
        try:
            await progress_msg.edit_text("❌ **Error occurred during processing**")
        except:
            pass
        return False
