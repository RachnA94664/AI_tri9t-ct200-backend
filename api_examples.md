# API Examples

## Browse
GET /browse/sections?version=latest
GET /browse/sections?version=v1
GET /browse/search?q=battery&version=latest
GET /browse/nodes/{node_id}/diff

## Selections
POST /selections
Body: {"name": "battery-and-alarms", "node_ids": [7, 15]}

GET /selections/{selection_id}