export { updateProcessingTable }

let PROCESSING_TABLE_NAME = "fullProcessingList"

function updateProcessingTable(msg_list) {
    console.log("Update table")
    const table = $(`#${PROCESSING_TABLE_NAME}`)

    msg_list.forEach( item => {
      console.log(`Process item: id=${item.id}`)

      let row = table.bootstrapTable('getRowByUniqueId', item.id)
      if (!row) {
        table.bootstrapTable('append', item)
      } else {
        table.bootstrapTable('updateByUniqueId', {
          id : item.id,
          row: item,
          replace: true
        })
      }
    })
  }
