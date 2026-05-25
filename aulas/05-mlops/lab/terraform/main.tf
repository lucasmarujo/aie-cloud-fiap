terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

resource "random_string" "sufixo" {
  length  = 6
  upper   = false
  special = false
}

locals {
  tags = {
    aula         = "5"
    disciplina   = "cloud-cognitive"
    projeto      = "quantum-commerce"
    provisionado = "terraform"
  }
}

data "azurerm_client_config" "current" {}

# Resource Group da Aula 5
resource "azurerm_resource_group" "rg" {
  name     = "rg-qc-aula05-${random_string.sufixo.result}"
  location = var.location
  tags     = local.tags
}

# Storage Account — datastore default do Workspace
resource "azurerm_storage_account" "ml" {
  name                     = "stml${random_string.sufixo.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  is_hns_enabled           = false # ML Workspace requer HNS desabilitado
  tags                     = local.tags
}

# Application Insights — dependência do Workspace
resource "azurerm_application_insights" "ml" {
  name                = "appi-ml-${random_string.sufixo.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  application_type    = "web"
  tags                = local.tags
}

# Key Vault — dependência do Workspace
resource "azurerm_key_vault" "ml" {
  name                       = "kvml${random_string.sufixo.result}"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  enable_rbac_authorization  = true
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  tags                       = local.tags
}

# Azure ML Workspace
resource "azurerm_machine_learning_workspace" "ws" {
  name                    = "mlw-qc-${random_string.sufixo.result}"
  resource_group_name     = azurerm_resource_group.rg.name
  location                = azurerm_resource_group.rg.location
  application_insights_id = azurerm_application_insights.ml.id
  key_vault_id            = azurerm_key_vault.ml.id
  storage_account_id      = azurerm_storage_account.ml.id

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# Compute Cluster com SCALE-TO-ZERO (0 nodes idle = custo zero)
resource "azurerm_machine_learning_compute_cluster" "cpu" {
  name                          = "cpu-cluster"
  location                      = azurerm_resource_group.rg.location
  vm_priority                   = "Dedicated"
  vm_size                       = "STANDARD_DS3_V2" # 4 vCPU, 14GB RAM
  machine_learning_workspace_id = azurerm_machine_learning_workspace.ws.id

  scale_settings {
    min_node_count                       = 0   # ← CRÍTICO: scale to zero
    max_node_count                       = 2
    scale_down_nodes_after_idle_duration = "PT2M" # 2 min idle → desliga
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}
