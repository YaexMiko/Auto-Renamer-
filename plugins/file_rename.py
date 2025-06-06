import asyncio
import logging
import os
import math
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import DARKXSIDE78
from plugins.auto_rename import auto_rename_file

# Store user states for file renaming
user_rename_states = {}

def get_readable_file_size(size_bytes):
    """Convert bytes to readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

async def clear_user_rename_state_after_timeout(user_id: int, timeout: int):
    """Clear user rename state after timeout"""
    await asyncio.sleep(timeout)
    if user_id in user_rename_states:
        del user_rename_states[user_id]

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_file_for_rename(client, message: Message):
    """Handle incoming files for renaming"""
    user_id = message.from_user.id
    
    # Get user settings
    settings = await DARKXSIDE78.get_user_settings(user_id)
    rename_mode = settings.get('rename_mode', 'Manual')
    
    # If Manual Mode is active, show direct rename prompt
    if rename_mode == "Manual":
        await show_direct_manual_rename(client, message)
        return
    
    # Try auto-rename for Auto modes
    auto_renamed = await auto_rename_file(client, message)
    
    # If auto-rename failed or not applicable, show manual rename
    if not auto_renamed:
        await show_direct_manual_rename(client, message)

async def show_direct_manual_rename(client, message: Message):
    """Show direct manual rename prompt"""
    user_id = message.from_user.id
    
    # Store file message for later processing
    user_rename_states[user_id] = {
        'original_message': message,
        'state': 'waiting_filename'
    }
    
    # Set timeout to clear state after 5 minutes
    asyncio.create_task(clear_user_rename_state_after_timeout(user_id, 300))
    
    # Send direct rename prompt
    rename_msg = await message.reply_text(
        "**✏️ Manual Rename Mode ✅**\n\n"
        "Send new file name with extension.\n\n"
        "**Note:** Don't delete your original file."
    )
    
    # Store the rename message for deletion
    user_rename_states[user_id]['rename_message'] = rename_msg

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "help", "settings", "autorename", "metadata", "tutorial", "token", "gentoken", "rename", "analyze", "batchrename", "set_caption", "del_caption", "see_caption", "viewthumb", "delthumb", "settitle", "setauthor", "setartist", "setaudio", "setsubtitle", "setvideo", "setencoded_by", "setcustom_tag"]))
async def handle_manual_rename_input(client, message: Message):
    """Handle manual rename filename input"""
    user_id = message.from_user.id
    
    # Check if user is in rename state
    if user_id not in user_rename_states:
        return
    
    state_info = user_rename_states[user_id]
    if state_info.get('state') != 'waiting_filename':
        return
    
    new_filename = message.text.strip()
    
    try:
        # Delete user's filename message immediately
        try:
            await message.delete()
        except:
            pass
        
        # Delete the rename prompt message
        try:
            rename_msg = state_info.get('rename_message')
            if rename_msg:
                await rename_msg.delete()
        except:
            pass
        
        # Validate filename
        if not new_filename or any(char in new_filename for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            error_msg = await client.send_message(
                message.chat.id,
                "❌ **Invalid filename!**\n\nFilename contains invalid characters or is empty."
            )
            await asyncio.sleep(3)
            await error_msg.delete()
            # Clear state
            if user_id in user_rename_states:
                del user_rename_states[user_id]
            return
        
        # Get original message
        original_msg = state_info.get('original_message')
        if not original_msg:
            if user_id in user_rename_states:
                del user_rename_states[user_id]
            return
        
        # Start rename and upload process
        success = await rename_and_upload_file_direct(client, original_msg, new_filename)
        
        # Clear state
        if user_id in user_rename_states:
            del user_rename_states[user_id]
        
    except Exception as e:
        logging.error(f"Manual rename input error: {e}")
        # Clear state on error
        if user_id in user_rename_states:
            del user_rename_states[user_id]

async def rename_and_upload_file_direct(client, message: Message, new_filename):
    """Rename and upload file directly with progress tracking"""
    try:
        user_id = message.from_user.id
        
        # Show progress message
        progress_msg = await client.send_message(
            message.chat.id,
            "📥 **Downloading file...**"
        )
        
        # Download file
        file_path = await message.download()
        
        if not file_path:
            await progress_msg.edit_text("❌ **Download failed!**")
            return False
        
        # Update progress
        await progress_msg.edit_text("🔄 **Renaming file...**")
        
        # Create new file path with new name
        directory = os.path.dirname(file_path)
        new_file_path = os.path.join(directory, new_filename)
        
        # Rename file
        os.rename(file_path, new_file_path)
        
        # Update progress
        await progress_msg.edit_text("📤 **Uploading file...**")
        
        # Get user settings for upload
        settings = await DARKXSIDE78.get_user_settings(user_id)
        thumbnail = await DARKXSIDE78.get_thumbnail(user_id)
        caption = await DARKXSIDE78.get_caption(user_id)
        
        # Prepare caption with variables
        final_caption = prepare_caption(caption, new_filename, message)
        
        # Upload based on file type and settings
        try:
            if message.document:
                if settings.get('send_as') == 'VIDEO' and new_filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')):
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
                if settings.get('send_as') == 'DOCUMENT':
                    await client.send_document(
                        chat_id=message.chat.id,
                        document=new_file_path,
                        caption=final_caption,
                        thumb=thumbnail
                    )
                else:
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
            
            # Update progress - success
            await progress_msg.edit_text(
                f"✅ **File renamed and uploaded successfully!**\n\n"
                f"**New Name:** `{new_filename}`"
            )
            
            # Clean up
            try:
                os.remove(new_file_path)
            except:
                pass
            
            # Update user stats
            try:
                await DARKXSIDE78.col.update_one(
                    {"_id": user_id},
                    {"$inc": {"rename_count": 1}}
                )
            except:
                pass
                
            return True
            
        except Exception as upload_error:
            logging.error(f"Upload error: {upload_error}")
            await progress_msg.edit_text(f"❌ **Upload failed:** {str(upload_error)}")
            
            # Clean up
            try:
                os.remove(new_file_path)
            except:
                pass
            
            return False
        
    except Exception as e:
        logging.error(f"Rename and upload error: {e}")
        try:
            await progress_msg.edit_text(f"❌ **Process failed:** {str(e)}")
        except:
            pass
        return False

def prepare_caption(caption_template, filename, message):
    """Prepare caption with variable substitution"""
    if not caption_template:
        return filename
    
    try:
        # Get file info
        file_size = 0
        duration = "Unknown"
        
        if message.document:
            file_size = message.document.file_size or 0
        elif message.video:
            file_size = message.video.file_size or 0
            duration = message.video.duration or 0
            if isinstance(duration, int):
                mins, secs = divmod(duration, 60)
                hours, mins = divmod(mins, 60)
                if hours:
                    duration = f"{hours:02d}:{mins:02d}:{secs:02d}"
                else:
                    duration = f"{mins:02d}:{secs:02d}"
        elif message.audio:
            file_size = message.audio.file_size or 0
            duration = message.audio.duration or 0
            if isinstance(duration, int):
                mins, secs = divmod(duration, 60)
                duration = f"{mins:02d}:{secs:02d}"
        
        # Convert file size to readable format
        readable_size = get_readable_file_size(file_size)
        
        # Replace variables in caption
        caption = caption_template.replace("{filename}", filename)
        caption = caption.replace("{filesize}", readable_size)
        caption = caption.replace("{duration}", str(duration))
        
        return caption
        
    except Exception as e:
        logging.error(f"Caption preparation error: {e}")
        return filename

# Alternative method for manual rename via command
@Client.on_message(filters.private & filters.command("rename"))
async def manual_rename_command(client, message: Message):
    """Manual rename command for direct filename input"""
    user_id = message.from_user.id
    
    # Check if user has sent a file recently
    if user_id not in user_rename_states:
        await message.reply_text(
            "❌ **No file to rename!**\n\n"
            "Please send a file first, then use this command."
        )
        return
    
    # Check command format
    if len(message.command) < 2:
        await message.reply_text(
            "❌ **Invalid format!**\n\n"
            "**Usage:** `/rename <new_filename>`\n"
            "**Example:** `/rename My Video.mp4`"
        )
        return
    
    # Get new filename from command
    new_filename = " ".join(message.command[1:]).strip()
    
    # Validate filename
    if not new_filename or any(char in new_filename for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
        await message.reply_text(
            "❌ **Invalid filename!**\n\n"
            "Filename contains invalid characters or is empty."
        )
        return
    
    # Get original message
    state_info = user_rename_states[user_id]
    original_msg = state_info.get('original_message')
    
    if not original_msg:
        await message.reply_text(
            "❌ **Original file not found!**\n\n"
            "Please send the file again."
        )
        if user_id in user_rename_states:
            del user_rename_states[user_id]
        return
    
    # Start rename process
    success = await rename_and_upload_file_direct(client, original_msg, new_filename)
    
    # Clear state
    if user_id in user_rename_states:
        del user_rename_states[user_id]
    
    if success:
        await message.reply_text("✅ **Rename completed successfully!**")
    else:
        await message.reply_text("❌ **Rename failed!**")
