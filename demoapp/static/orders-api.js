import { apiGet, apiPostItem, apiDelete, webSocketConnect, getWebsocketInfo, HTTPError, appSettings } from "/static/api-base.js"

export { getCustomers, getProductItems, createNewOrder, getUserInfo, getOrders, deleteOrders, generateTestOrders, getWebsocketInfo, webSocketConnect }

async function getCustomers() {
    return await apiGet("/api/customers")
}

async function getProductItems() {
    return await apiGet("/api/product-items")
}

async function createNewOrder(order) {
    try {
        return await apiPostItem("/api/orders", order)
    } catch(err) {
        if (err instanceof HTTPError) {
            if (err.code == 401) {
                console.log(`Redirect to login URL: ${appSettings.loginUrl}`)
                window.location.href = appSettings.loginUrl
            }
        }
    }
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
