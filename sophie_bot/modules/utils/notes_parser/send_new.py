from typing import Tuple, Optional

from aiogram.types import Message, MessageId, User, InputMedia

from sophie_bot import bot
from sophie_bot.models.notes import BaseNote
from sophie_bot.types.chat import ChatId
from .text import vars_parser, random_parser

MULTI_MESSAGE_FILE = ('sticker', 'video_note')
FILE_TYPES_NO_PREVIEW = ['animation']
FILE_TYPES_FUNCS = {
    'photo': bot.send_photo,
    'sticker': bot.send_sticker,
    'audio': bot.send_audio,
    'video_note': bot.send_video_note,
    'voice': bot.send_voice,
    'animation': bot.send_animation,
    'document': bot.send_document
}


async def send_new_note(
        send_id: ChatId,
        note: BaseNote,
        reply_to: MessageId,
        raw: bool = False,
        message: Optional[Message] = None,
        user: Optional[User] = None
) -> Tuple[Message, ...]:
    # TODO: Make media group text be in the same message if there is no keyboard

    # Text processing
    text = note.text or ''
    if raw and message:
        text = await vars_parser(
            random_parser(text),
            message,
            user=user or message.from_user
        )

    parse_mode = note.parse_mode.value

    if note.file:
        file_type = note.file.type
        file_id = note.file.id
    else:
        file_type = None

    # Send a multi message
    media_group: bool = type(file_id) is list
    multi_message: bool = text and note.file and note.file.type in MULTI_MESSAGE_FILE or media_group

    msgs: Tuple[Message, ...] = ()
    if file_type:
        kwargs = {
            'reply_to_message_id': reply_to
        }

        if not media_group:
            kwargs['reply_markup'] = None

        if file_type not in MULTI_MESSAGE_FILE and not media_group:
            kwargs['parse_mode'] = parse_mode
            kwargs['caption'] = text
            if file_type not in FILE_TYPES_NO_PREVIEW:
                kwargs['disable_web_page_preview'] = note.preview

        if media_group:
            # Send a media group
            msgs = (await bot.send_media_group(
                send_id,
                [InputMedia(type=note.file.type, media=x) for x in file_id],
                **kwargs
            ))
        else:
            # Send a media
            msgs = (await FILE_TYPES_FUNCS[file_type](
                send_id,
                file_id,
                **kwargs
            ))

    if multi_message:
        # Unsets reply_to, as we already replied to a message with above media message
        reply_to = None

    # Send text message
    if not file_type or multi_message:
        return (*msgs, await bot.send_message(
            chat_id=send_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=None,
            reply_to_message_id=reply_to,
            disable_web_page_preview=note.preview
        ))

    return msgs
