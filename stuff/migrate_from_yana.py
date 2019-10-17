# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2019 MrYacha
# Copyright (C) 2018 - 2019 Paul Larsen (Marie)
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from time import gmtime, strftime

from sophie_bot import mongodb

import threading
from typing import Union

from sqlalchemy import Column, String, Boolean, UnicodeText, Integer, func, distinct

from telethon import custom

DB_URI = 'postgresql://yacha:q@localhost:5432/y2'


def start() -> scoped_session:
    engine = create_engine(DB_URI, client_encoding="utf8")
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


BASE = declarative_base()
SESSION = start()


class Notes(BASE):
    __tablename__ = "notes"
    chat_id = Column(String(14), primary_key=True)
    name = Column(UnicodeText, primary_key=True)
    value = Column(UnicodeText, nullable=False)
    file = Column(UnicodeText)
    is_reply = Column(Boolean, default=False)
    has_buttons = Column(Boolean, default=False)
    msgtype = Column(Integer, default=False)

    def __init__(self, chat_id, name, value, msgtype, file=None):
        self.chat_id = str(chat_id)  # ensure string
        self.name = name
        self.value = value
        self.msgtype = msgtype
        self.file = file

    def __repr__(self):
        return "<Note %s>" % self.name


class Buttons(BASE):
    __tablename__ = "note_urls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), primary_key=True)
    note_name = Column(UnicodeText, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    url = Column(UnicodeText, nullable=False)
    same_line = Column(Boolean, default=False)

    def __init__(self, chat_id, note_name, name, url, same_line=False):
        self.chat_id = str(chat_id)
        self.note_name = note_name
        self.name = name
        self.url = url
        self.same_line = same_line


Notes.__table__.create(checkfirst=True)
Buttons.__table__.create(checkfirst=True)

NOTES_INSERTION_LOCK = threading.RLock()
BUTTONS_INSERTION_LOCK = threading.RLock()


def get_note(chat_id, note_name):
    try:
        return SESSION.query(Notes).get((str(chat_id), note_name))
    finally:
        SESSION.close()


def get_all_chat_notes(chat_id):
    try:
        return SESSION.query(Notes).filter(Notes.chat_id == str(chat_id)).order_by(Notes.name.asc()).all()
    finally:
        SESSION.close()


def get_buttons(chat_id, note_name):
    try:
        return SESSION.query(Buttons).filter(Buttons.chat_id == str(chat_id), Buttons.note_name == note_name).order_by(
            Buttons.id).all()
    finally:
        SESSION.close()


def build_keyboard(buttons):
    keyb = []
    for btn in buttons:
        if btn.same_line and keyb:
            keyb[-1].append(custom.Button.url(btn.name, btn.url))
        else:
            keyb.append([custom.Button.url(btn.name, btn.url)])

    return keyb


def build_text_keyboard(buttons, text):
    txt = text
    for btn in buttons:
        if btn.same_line and txt:
            txt += f"[{btn.name}](buttonurl:{btn.url}:same)\n"
        else:
            txt += f"[{btn.name}](buttonurl:{btn.url})\n"

    return txt


mongodb.yana_notes.drop()
all_chats = mongodb.chat_list.find()
chat_num = 0
for chat in all_chats:
    chat_num += 1
    chat_id = chat['chat_id']
    all_notes_pq = get_all_chat_notes(chat_id)
    all_notes_md = mongodb.notes.find({'chat_id': chat_id})
    num = 0
    for note in all_notes_pq:
        num += 1
        if note.name.lower() in [d['name'].lower() for d in all_notes_md]:
            print(f'Dont update note {note.name}')
            continue

        print("==================")
        print(f"{num}/{len(all_notes_pq)} | {chat_num}/{all_chats.count()}")
        print(note.name)
        pnote = get_note(chat_id, note.name)
        btns = get_buttons(chat_id, note.name)
        ptext = pnote.value + "\n"
        if btns:
            print(f"Note {note.name} have buttons!")
            ptext = build_text_keyboard(btns, ptext)

        #print(ptext)

        if not note.file:
            file = None
        else:
            print("This note has file!")
            print(note.file)

        date = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        new = {
            'chat_id': chat_id,
            'name': note.name.lower(),
            'text': ptext,
            'created': date,
            'file_id': file,
        }

        print(new)

        print("Uploading to MongoDB...")
        mongodb.yana_notes.insert(new)

        print("==================")