from common_layer.common_schemas.user_schema import UserTypes
permissions = {
    UserTypes.SUPER_ADMIN: {
        "dashboard": "crud",
        "users": "crud",
        "staff": "crud",
        "customers": "crud",
        "settings": "crud",
        "property": "crud",
        "chat": "crud",
    },
    UserTypes.STAFF: {
        "dashboard": "crud",
        "users": "crud",
        "staff": "crud",
        "customers": "crud",
        "settings": "crud",
        "property": "crud",
        "chat": "crud",
    },
    UserTypes.CUSTOMER: {
        "dashboard": "",
        "users": "",
        "staff": "",
        "customers": "",
        "settings": "",
        "property": "",
        "chat": ""
    },
    UserTypes.PARTNER: {
        "dashboard": "",
        "users": "",
        "staff": "",
        "customers": "",
        "settings": "",
        "property": "crud",
        "chat": "crud"
    },
}
