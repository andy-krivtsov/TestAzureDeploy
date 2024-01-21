import { apiGet, apiPostItem, apiDelete, webSocketConnect, getWebsocketInfo } from "/static/api-base.js"
export { deleteProcessingItems, generateTestItems, webSocketConnect, getWebsocketInfo }

async function deleteProcessingItems() {
    return apiDelete("/api/processing")
}

async function generateTestItems() {
    return apiPostItem("api/commands/generate-items", {})
}
