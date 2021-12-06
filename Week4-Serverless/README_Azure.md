# Assignment-4 Serverless

## Azure Functions

To start working with IntelliJ, read this [website](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-maven-intellij) to start:

In order to set up the local environment for Azure Functions, we need to follow [this webstie](https://docs.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-java?tabs=bash%2Cazure-cli%2Cbrowser):
1. Install Azure Functions Core Tools version 4.x
2. Install Azure CLI version 2.4.X +
3. Have Java Developer Kit version 8 or 11
4. Have Maven in the local File Path version 3.0 +

To check if we satisfied the request or not:
1. use `func --version` to check core tool version (might also need to install DotNet)
2. Must install the 64 bits core tools: [Windows 64-bit](https://go.microsoft.com/fwlink/?linkid=2174087) (VS Code debugging requires 64-bit), otherwise, it will not run
3. use `az --version` to check Azure CLI version
4. My local JAVA_Home is `"C:\Program Files\Java\jdk-11.0.2\bin\java"`, this information need to be updated to the `C:\Users\Zhuzhu\AppData\Roaming\npm\node_modules\azure-functions-core-tools\bin\workers\java` folder's `worker.config.json` file
5. `host.json` file's extensionBundle version need to be set as `[3.*, 4.00)`


This is the link for connect Azure Functions to cloud: [website](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=v4%2Cwindows%2Cjava%2Cportal%2Cbash%2Ckeda)

This is the [Chinese Version](https://docs.microsoft.com/zh-cn/azure/azure-functions/functions-reference?tabs=blob)

In order to simulate a local blob and queue environment, we need to install azurite on our computer:

`npm install  -g azurite`

Then, to start the local storage environment, we use the command "azurite start"


[This](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-storage-blob-triggered-function) is an example about how to use C# to detect blob storage change.