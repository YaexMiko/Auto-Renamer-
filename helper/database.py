import motor.motor_asyncio
import datetime
import pytz
from config import Config
import logging

class Database:
    def __init__(self, uri, database_name):
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            self._client.server_info()
            logging.info("Successfully connected to MongoDB")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise e
        self.DARKXSIDE78 = self._client[database_name]
        self.col = self.DARKXSIDE78.user
        self.token_links = self.DARKXSIDE78.token_links

    def new_user(self, id):
        return dict(
            _id=int(id),
            join_date=datetime.datetime.now(pytz.utc).date().isoformat(),
            file_id=None,
            caption=None,
            metadata="Off",
            metadata_code="Telegram : @DARKXSIDE78",
            format_template=None,
            rename_count=0,
            first_name="",
            username="",
            token_tasks=[],
            is_premium=False,
            premium_expiry=None,
            token=69,
            media_type=None,
            title='GenAnimeOfc [t.me/GenAnimeOfc]',
            author='DARKXSIDE78',
            artist='DARKXSIDE78',
            audio='[GenAnimeOfc]',
            subtitle="[GenAnimeOfc]",
            video='[GenAnimeOfc]',
            encoded_by="GenAnimeOfc [DARKXSIDE78]",
            custom_tag="[GenAnimeOfc]",
            upload_mode='Telegram',
            send_as='DOCUMENT',
            upload_destination=None,
            prefix=None,
            suffix=None,
            rename_mode='Manual',
            remove_words=None,
            sample_video=False,
            screenshot_enabled=False,
            manual_mode=True,
            ban_status=dict(
                is_banned=False,
                ban_duration=0,
                banned_on=datetime.datetime.max.date().isoformat(),
                ban_reason=''
            )
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            user["first_name"] = u.first_name or "Unknown"
            user["username"] = u.username or ""
            try:
                await self.col.insert_one(user)
                logging.info(f"User {u.id} added to database")
            except Exception as e:
                logging.error(f"Error adding user {u.id} to database: {e}")

    async def is_user_exist(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return bool(user)
        except Exception as e:
            logging.error(f"Error checking if user {id} exists: {e}")
            return False

    async def total_users_count(self):
        try:
            count = await self.col.count_documents({})
            return count
        except Exception as e:
            logging.error(f"Error counting users: {e}")
            return 0

    async def get_all_users(self):
        try:
            all_users = self.col.find({})
            return all_users
        except Exception as e:
            logging.error(f"Error getting all users: {e}")
            return None

    async def delete_user(self, user_id):
        try:
            await self.col.delete_many({"_id": int(user_id)})
        except Exception as e:
            logging.error(f"Error deleting user {user_id}: {e}")

    async def set_thumbnail(self, id, file_id):
        try:
            await self.col.update_one({"_id": int(id)}, {"$set": {"file_id": file_id}})
        except Exception as e:
            logging.error(f"Error setting thumbnail for user {id}: {e}")

    async def get_thumbnail(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("file_id", None) if user else None
        except Exception as e:
            logging.error(f"Error getting thumbnail for user {id}: {e}")
            return None

    async def set_caption(self, id, caption):
        try:
            await self.col.update_one({"_id": int(id)}, {"$set": {"caption": caption}})
        except Exception as e:
            logging.error(f"Error setting caption for user {id}: {e}")

    async def get_caption(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("caption", None) if user else None
        except Exception as e:
            logging.error(f"Error getting caption for user {id}: {e}")
            return None

    async def set_format_template(self, id, format_template):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"format_template": format_template}}
            )
        except Exception as e:
            logging.error(f"Error setting format template for user {id}: {e}")

    async def get_format_template(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("format_template", None) if user else None
        except Exception as e:
            logging.error(f"Error getting format template for user {id}: {e}")
            return None

    async def create_token_link(self, user_id: int, token_id: str, tokens: int):
        expiry = datetime.datetime.now(pytz.utc) + datetime.timedelta(hours=24)
        try:
            await self.token_links.update_one(
                {"_id": token_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "tokens": tokens,
                        "created_at": datetime.datetime.now(pytz.utc),
                        "expires_at": expiry,
                        "claimed": False
                    }
                },
                upsert=True
            )
        except Exception as e:
            logging.error(f"Error creating token link: {e}")

    async def claim_token_link(self, token_id: str, claimer_id: int):
        try:
            token_data = await self.token_links.find_one({"_id": token_id})
            if not token_data:
                return {"success": False, "message": "Invalid token link"}
            
            if token_data["claimed"]:
                return {"success": False, "message": "Token already claimed"}
            
            if datetime.datetime.now(pytz.utc) > token_data["expires_at"]:
                return {"success": False, "message": "Token link expired"}
            
            if token_data["user_id"] == claimer_id:
                return {"success": False, "message": "Cannot claim your own token"}
            
            await self.token_links.update_one(
                {"_id": token_id},
                {"$set": {"claimed": True, "claimed_by": claimer_id, "claimed_at": datetime.datetime.now(pytz.utc)}}
            )
            
            await self.col.update_one(
                {"_id": claimer_id},
                {"$inc": {"token": token_data["tokens"]}}
            )
            
            return {"success": True, "tokens": token_data["tokens"]}
            
        except Exception as e:
            logging.error(f"Error claiming token: {e}")
            return {"success": False, "message": "Database error"}

    async def get_user_settings(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            if not user:
                return {}
            
            return {
                'upload_mode': user.get('upload_mode', 'Telegram'),
                'send_as': user.get('send_as', 'DOCUMENT'),
                'upload_destination': user.get('upload_destination'),
                'prefix': user.get('prefix'),
                'suffix': user.get('suffix'),
                'rename_mode': user.get('rename_mode', 'Manual'),
                'remove_words': user.get('remove_words'),
                'sample_video': user.get('sample_video', False),
                'screenshot_enabled': user.get('screenshot_enabled', False),
                'manual_mode': user.get('manual_mode', True)
            }
        except Exception as e:
            logging.error(f"Error getting user settings: {e}")
            return {}

    async def update_user_setting(self, user_id, setting_name, value):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {setting_name: value}}
            )
        except Exception as e:
            logging.error(f"Error updating user setting: {e}")

    async def get_prefix(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('prefix') if user else None
        except Exception as e:
            logging.error(f"Error getting prefix: {e}")
            return None

    async def set_prefix(self, user_id, prefix):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"prefix": prefix}}
            )
        except Exception as e:
            logging.error(f"Error setting prefix: {e}")

    async def get_suffix(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('suffix') if user else None
        except Exception as e:
            logging.error(f"Error getting suffix: {e}")
            return None

    async def set_suffix(self, user_id, suffix):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"suffix": suffix}}
            )
        except Exception as e:
            logging.error(f"Error setting suffix: {e}")

    async def get_remove_words(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('remove_words') if user else None
        except Exception as e:
            logging.error(f"Error getting remove words: {e}")
            return None

    async def set_remove_words(self, user_id, words):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"remove_words": words}}
            )
        except Exception as e:
            logging.error(f"Error setting remove words: {e}")

    async def get_metadata(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('metadata', 'Off') if user else 'Off'
        except Exception as e:
            logging.error(f"Error getting metadata: {e}")
            return 'Off'

    async def set_metadata(self, user_id, status):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"metadata": status}}
            )
        except Exception as e:
            logging.error(f"Error setting metadata: {e}")

    async def get_title(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('title') if user else None
        except Exception as e:
            return None

    async def set_title(self, user_id, title):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"title": title}}
            )
        except Exception as e:
            logging.error(f"Error setting title: {e}")

    async def get_author(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('author') if user else None
        except Exception as e:
            return None

    async def set_author(self, user_id, author):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"author": author}}
            )
        except Exception as e:
            logging.error(f"Error setting author: {e}")

    async def get_artist(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('artist') if user else None
        except Exception as e:
            return None

    async def set_artist(self, user_id, artist):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"artist": artist}}
            )
        except Exception as e:
            logging.error(f"Error setting artist: {e}")

    async def get_audio(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('audio') if user else None
        except Exception as e:
            return None

    async def set_audio(self, user_id, audio):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"audio": audio}}
            )
        except Exception as e:
            logging.error(f"Error setting audio: {e}")

    async def get_subtitle(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('subtitle') if user else None
        except Exception as e:
            return None

    async def set_subtitle(self, user_id, subtitle):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"subtitle": subtitle}}
            )
        except Exception as e:
            logging.error(f"Error setting subtitle: {e}")

    async def get_video(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('video') if user else None
        except Exception as e:
            return None

    async def set_video(self, user_id, video):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"video": video}}
            )
        except Exception as e:
            logging.error(f"Error setting video: {e}")

    async def get_encoded_by(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('encoded_by') if user else None
        except Exception as e:
            return None

    async def set_encoded_by(self, user_id, encoded_by):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"encoded_by": encoded_by}}
            )
        except Exception as e:
            logging.error(f"Error setting encoded_by: {e}")

    async def get_custom_tag(self, user_id):
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get('custom_tag') if user else None
        except Exception as e:
            return None

    async def set_custom_tag(self, user_id, custom_tag):
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"custom_tag": custom_tag}}
            )
        except Exception as e:
            logging.error(f"Error setting custom_tag: {e}")

DARKXSIDE78 = Database(Config.DB_URL, Config.DB_NAME)
