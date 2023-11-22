metadata description = 'Creates new Container App Environment and support services'

param location string = resourceGroup().location
param environmentName string = 'MyDemoContEnv'
param logWorkspaceName string = 'conapp-logs-${uniqueString(resourceGroup().id)}'
param storageAccountName string = 'conappstor${uniqueString(resourceGroup().id)}'
param storageShareName string = 'containerapps'

resource storacc 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
  }

  resource fileservice 'fileServices' = {
    name: 'default'
    resource appshare 'shares' = {
      name: storageShareName
    }
  }
}

resource logs 'Microsoft.OperationalInsights/workspaces@2021-12-01-preview' = {
  name: logWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource appenv 'Microsoft.App/managedEnvironments@2023-05-02-preview' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listkeys('2015-11-01-preview').primarySharedKey
      }
    }
  }
  resource appfiles 'storages' = {
    name: 'azurefiles'
    properties: {
      azureFile: {
        accountName: storageAccountName
        accountKey: storacc.listKeys().keys[0].value
        shareName: storageShareName
        accessMode: 'ReadWrite'
      }
    }
  }
}
