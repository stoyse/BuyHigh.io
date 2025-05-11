buyhigh-io-db/
├── chats/
│   ├── chat_id_1/
│   │   ├── name: "General"
│   │   ├── created_at: timestamp
│   │   ├── created_by: user_id
│   │   └── members_can_invite: false
│   └── chat_id_2/
│       └── ...
├── chat_participants/
│   ├── chat_id_1/
│   │   ├── user_id_1/
│   │   │   ├── chat_name: "username1"
│   │   │   └── joined_at: timestamp
│   │   └── user_id_2/
│   │       └── ...
│   └── chat_id_2/
│       └── ...
└── messages/
    ├── chat_id_1/
    │   ├── message_id_1/
    │   │   ├── user_id: user_id_1
    │   │   ├── message_text: "Hello, world!"
    │   │   └── sent_at: timestamp
    │   └── message_id_2/
    │       └── ...
    └── chat_id_2/
        └── ...