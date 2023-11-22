metadata description = 'Creates new Container App'

param location string = resourceGroup().location
param containerappName string = 'python-demo-app'
param environmentName string = 'MyDemoContEnv'
param containerImage string = 'learn/demo-python'
param containerTag string = '1.0.0'
param registryName string = 'akazureregistry.azurecr.io'
param identityName string = 'DemoContainerApp2'

var fullImageName = '${registryName}/${containerImage}:${containerTag}'
var identityId = resourceId('Microsoft.ManagedIdentity/userAssignedIdentities', identityName)

resource appenv 'Microsoft.App/managedEnvironments@2023-05-02-preview' existing = {
  name: environmentName
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
