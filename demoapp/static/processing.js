export { updateProcessingTable, processingTimeFormat, updateRemainingTime, processingRowStyle }

let PROCESSING_TABLE_NAME = "fullProcessingList"
let UPDATE_TIME_DELAY = 1000

function updateProcessingTable(msg_list) {
    const table = $(`#${PROCESSING_TABLE_NAME}`)

    msg_list.forEach(item => {
        let row = table.bootstrapTable('getRowByUniqueId', item.id)
        if (!row) {
            table.bootstrapTable('append', item)
        } else {
            table.bootstrapTable('updateByUniqueId', {
                id: item.id,
                row: item,
                replace: true
            })
        }
    })
}

function processingTimeFormat(value, item) {
    if (item.remaining) {
        return String(item.remaining)
    }
    return String(item.processingTime)
}

async function updateRemainingTime() {
    let table = $(`#fullProcessingList`)
    let data = table.bootstrapTable('getData')

    data.filter(item => item.status == "Processing").forEach(item => {
        let update = false

        if (!item.started) { return }

        if (!item.expected_finish_time) {
            let d = new Date(item.started)
            d.setSeconds(d.getSeconds() + item.processingTime)
            item.expected_finish_time = d.valueOf()
            update = true
        }

        let remaining = Math.round((item.expected_finish_time - new Date().valueOf()) / 1000)
        if (remaining >= 0 && remaining != item.remaining) {
            item.remaining = remaining
            update = true
        }

        if (update) {
            table.bootstrapTable('updateByUniqueId', {
                id: item.id,
                row: item,
                replace: true
            })
        }
    })

    setTimeout(updateRemainingTime, UPDATE_TIME_DELAY)
}

function processingRowStyle(value, item) {
    let ret = {}
    if (item.status == "Processing") {
        ret.classes = "bg-warning text-dark"
    }
    if (item.status == "Recovery") {
        ret.classes = "bg-danger text-white"
    }

    return ret
}