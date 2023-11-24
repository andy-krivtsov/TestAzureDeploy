metadata description = 'Creates new Container App Environment, support services and demo application'

param location string = resourceGroup().location
param environmentName string = 'MyDemoContEnv'
param logWorkspaceName string = 'conapp-logs-${uniqueString(resourceGroup().id)}'
param storageAccountName string = 'conappstor${uniqueString(resourceGroup().id)}'
param storageShareName string = 'containerapps'
param containerappName string = 'python-demo-app'
param containerImage string = 'learn/demo-python'
param containerTag string = 'dev'
param commitSha string = '000000'
param buildId string = '0'
param registryName string = 'akazureregistry.azurecr.io'
param identityName string = 'DemoContainerApp'

var fullImageName = '${registryName}/${containerImage}:${containerTag}'
var identityId = resourceId('Microsoft.ManagedIdentity/userAssignedIdentities', identityName)
var revisionSuffix = '${buildId}-${take(commitSha, 10)}'

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

resource contapp 'Microsoft.App/containerApps@2023-05-02-preview' = {
  name: containerappName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}' : {}
    }
  }
  properties: {
    managedEnvironmentId: appenv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
        transport: 'auto'
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: registryName
          identity: identityId
        }
      ]
    }
    template: {
      revisionSuffix: revisionSuffix
      containers: [
        {
          name: containerappName
          image: fullImageName
          resources: {
            cpu: '0.25'
            memory: '0.5Gi'
          }
          probes: [
            {
              type: 'liveness'
              httpGet: {
                path: '/'
                port: 8000
              }
              initialDelaySeconds: 7
              periodSeconds: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}
