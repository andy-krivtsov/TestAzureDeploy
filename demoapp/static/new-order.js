import { getCustomers, getProductItems, createNewOrder, getOrders } from '/static/orders-api.js'
import { generateUUID, randomInt } from '/static/utils.js'
import { datetimeFormat } from '/static/utils.js'

export { setupNewOrderForm, onNewOrder, onGenerateRandomOrder, updateActiveOrdersTable };

export let newOrderFormModel = getEmptyOrderModel()

export let customersList = []
export let productItemList = []

let ACTIVE_ORDERS_TABLE_NAME = "currentOrders"

function getEmptyOrderModel() {
    return {
        id: "",
        created: new Date(),
        customer: { id: "", name: "" },
        items: [
            {
                item: { id: "", name: "" },
                count: 0
            },
            {
                item: { id: "", name: "" },
                count: 0
            }
        ],
        dueDate: new Date(),
        status: ""
    }
}

function getRandomOrderModel() {
    let d = new Date()
    d.setUTCDate(d.getUTCDate() + randomInt(1, 120))

    const model = getEmptyOrderModel()
    model.id = generateUUID()
    model.created = new Date()
    model.customer = customersList[randomInt(0, customersList.length-1)]
    console.log(`Customer list: ${customersList.length}, selected: ${model.customer.name} `)

    for (let i = 0; i <= 1; i++) {
        model.items[i].item = productItemList[randomInt(0, productItemList.length-1)]
        model.items[i].count = randomInt(0, 50)
    }
    model.dueDate = d

    return model
}

function getFormElements() {
    const inputs = [ 'orderId', 'orderDate',  'customerName', 'itemType1', 'itemType2', 'itemNumber1', 'itemNumber2', 'dueDate' ]
    return Object.fromEntries(inputs.map( x => [x, document.getElementById(x)]))
}

function newSelectOption(value, text) {
    const opt = document.createElement("option")
    opt.value = value
    opt.textContent = text
    return opt
}

function loadOrderFormSelections() {
    const customerSelect = document.getElementById("customerName")
    customersList.forEach(x => customerSelect.append(newSelectOption(x.id, x.name)))

    const itemSelect1 = document.getElementById("itemType1")
    const itemSelect2 = document.getElementById("itemType2")

    productItemList.forEach(x => {
        itemSelect1.append(newSelectOption(x.id, x.name))
        itemSelect2.append(newSelectOption(x.id, x.name))
    })
}

// Model => page Form
function loadOrderForm() {
    const elems = getFormElements()

    elems["orderId"].value = newOrderFormModel.id
    elems['orderDate'].value = newOrderFormModel.created.toISOString().split('T')[0]

    elems["customerName"].value = newOrderFormModel.customer.id

    for (let i = 0; i <= 1; i++) {
        elems[`itemType${i+1}`].value = newOrderFormModel.items[i].item.id
        elems[`itemNumber${i+1}`].value = newOrderFormModel.items[i].count
    }

    elems['dueDate'].value = newOrderFormModel.dueDate.toISOString().split('T')[0]
}

// Page Form => Model
function saveOrderModel() {
    const elems = getFormElements()

    let model = getEmptyOrderModel()

    model.id = elems["orderId"].value
    model.created = new Date()
    model.customer = customersList.find(x => x.id == elems["customerName"].value)

    for (let i = 0; i <= 1; i++) {
        model.items[i].item = productItemList.find(x => x.id == elems[`itemType${i+1}`].value)
        model.items[i].count = elems[`itemNumber${i+1}`].valueAsNumber
    }

    model.dueDate = elems['dueDate'].valueAsDate
    model.status = 'New'

    newOrderFormModel = model
}

async function setupNewOrderForm() {
    customersList = await getCustomers()
    productItemList = await getProductItems()

    loadOrderFormSelections()

    let d = new Date()
    d.setUTCDate(d.getUTCDate() + 60)
    newOrderFormModel.dueDate = d

    loadOrderForm()
}

function validateOrder(order) {
    let errs = []
    if (!order.id)
        errs.push("Order is null")

    if (!order.customer)
        errs.push("Customer is null")

    order.items.forEach(x => {
        if (!x)
            errs.push("Item is null")
    })

    if (errs.length)
        throw { "message": "Order validation error!", "errors": errs }
}

async function onNewOrder() {
    saveOrderModel()
    console.log(`New order: ${JSON.stringify(newOrderFormModel)}`)

    validateOrder(newOrderFormModel)
    await createNewOrder(newOrderFormModel)

    //$(`#currentOrders`).bootstrapTable('refresh')

    newOrderFormModel.id = ""
    loadOrderForm()
}

function onGenerateRandomOrder() {
    newOrderFormModel = getRandomOrderModel()
    loadOrderForm()
}

function updateActiveOrdersTable(msg_list) {
    console.log("Update table")
    const table = $(`#${ACTIVE_ORDERS_TABLE_NAME}`)

    msg_list.forEach( order => {
      console.log(`Process order: id=${order.id}`)

      let row = table.bootstrapTable('getRowByUniqueId', order.id)
      if (!row) {
        table.bootstrapTable('append', order)
      } else {
        table.bootstrapTable('updateByUniqueId', {
          id : order.id,
          row: order,
          replace: true
        })
      }
    })
  }
