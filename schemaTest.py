todo_schema = {
    "type": "object",
    "required": ["username", "password"],
    "properties": {
        "handle": {
            "type": "string",
            "description": "User Handle",
            "maxLength": 35,
            "minLength": 3,
            "default": "",
            "example": "Fahad",
            "pattern": "^[A-Za-z0-9]*$"
        },
        "password": {
            "type": "string",
            "description": "User Password",
            "default": "",
            "minLength": 8,
            "example": "12343@",
            "pattern": "^(.*)$"
        },

        "retypepassword": {
            "type": "string",
            "description": "User Password",
            "default": "",
            "minLength": 8,
            "example": "12343@",
            "pattern": "^(.*)$"
        }
    }
}