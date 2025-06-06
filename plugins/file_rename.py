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
    
    # Try auto-rename for Auto mode
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
    
    # Set timeout
    asyncio.create_task(clear_user_rename_state_after_timeout(user_id, 60))
    
    # Send direct rename prompt
    rename_msg = await message.reply_text(
        "**✏️ Manual Rename Mode ✅**\n\n"
        "Send New file name with extension.\n\n"
        "**Note:** Don't delete your original file."
    )
    
    # Store the rename message for deletion
    user_rename_states[user_id]['rename_message'] = rename_msg

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "help", "settings", "autorename", "metadata", "tutorial", "token", "gentoken", "rename", "analyze", "batchrename"]))
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
            error_msg = await message.reply_text("❌ **Invalid filename!**\n\nFilename contains invalid characters.")
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
    """Rename and upload file directly without status messages"""
    try:
        user_id = message.from_user.id
        
        # Start downloading immediately
        file_path = await message.download()
        
        # Create new file path with new name
        directory = os.path.dirname(file_path)
        new_file_path = os.path.join(directory, new_filename)
        
        # Rename file
        os.rename(file_path, new_file_path)
        
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
        
        return True
        
    except Exception as e:
        logging.error(f"Error in direct rename and upload: {e}")
        return False

async def apply_metadata_to_file(file_path, user_id):
    """Apply metadata to file if enabled"""
    try:
        metadata_status = await DARKXSIDE78.get_metadata(user_id)
        if metadata_status == "Off":
            return file_path
        
        # Get metadata values
        title = await DARKXSIDE78.get_title(user_id)
        author = await DARKXSIDE78.get_author(user_id)
        artist = await DARKXSIDE78.get_artist(user_id)
        audio = await DARKXSIDE78.get_audio(user_id)
        subtitle = await DARKXSIDE78.get_subtitle(user_id)
        video = await DARKXSIDE78.get_video(user_id)
        encoded_by = await DARKXSIDE78.get_encoded_by(user_id)
        custom_tag = await DARKXSIDE78.get_custom_tag(user_id)
        
        # Create metadata command
        metadata_cmd = ["ffmpeg", "-i", file_path]
        
        # Add metadata options
        if title:
            metadata_cmd.extend(["-metadata", f"title={title}"])
        if author:
            metadata_cmd.extend(["-metadata", f"author={author}"])
        if artist:
            metadata_cmd.extend(["-metadata", f"artist={artist}"])
        if audio:
            metadata_cmd.extend(["-metadata", f"audio={audio}"])
        if subtitle:
            metadata_cmd.extend(["-metadata", f"subtitle={subtitle}"])
        if video:
            metadata_cmd.extend(["-metadata", f"video={video}"])
        if encoded_by:
            metadata_cmd.extend(["-metadata", f"encoded_by={encoded_by}"])
        if custom_tag:
            metadata_cmd.extend(["-metadata", f"comment={custom_tag}"])
        
        # Output file
        output_path = file_path.replace(".mp4", "_metadata.mp4")
        metadata_cmd.extend(["-c", "copy", output_path])
        
        # Run ffmpeg command (simplified for this example)
        # In production, you would use subprocess.run or asyncio.subprocess
        
        return output_path if os.path.exists(output_path) else file_path
        
    except Exception as e:
        logging.error(f"Error applying metadata: {e}")
        return file_path
