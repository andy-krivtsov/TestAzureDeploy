import { apiGet, apiPostItem, apiDelete, webSocketConnect, getWebsocketInfo } from "/static/api-base.js"

export { getCustomers, getProductItems, createNewOrder, getUserInfo, getOrders, deleteOrders, generateTestOrders, getWebsocketInfo, webSocketConnect }

async function getCustomers() {
    return await apiGet("/api/customers")
}

async function getProductItems() {
    return await apiGet("/api/product-items")
}

async function createNewOrder(order) {
    return apiPostItem("/api/orders", order)
}

async function getOrders() {
    return apiGet("/api/orders")
}

async function deleteOrders() {
    return apiDelete("/api/orders")
}

async function generateTestOrders() {
    return apiPostItem("api/commands/generate-orders", {})
}

async function getUserInfo() {
    return await apiGet("/api/userinfo")
}
