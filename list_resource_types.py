import json
from collections import Counter, defaultdict
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient
import asyncio
import aiohttp
from typing import Dict, List, Tuple

class AzureResourceTypeAnalyzer:
    """
    Analyzes Azure resource types across specified subscriptions in a tenant.
    Groups resources by type, counts them, and provides descriptions.
    """
    
    def __init__(self, target_subscriptions: List[str] = None):
        """Initialize the Azure clients with default credentials."""
        try:
            # self.credential = DefaultAzureCredential()
            self.credential = InteractiveBrowserCredential()
            self.subscription_client = SubscriptionClient(self.credential)
            self.resource_descriptions = {}
            self.target_subscriptions = target_subscriptions or []
        except Exception as e:
            print(f"Error initializing Azure credentials: {e}")
            raise

    def get_subscriptions(self) -> List[str]:
        """
        Get specified subscriptions that exist and are enabled in the tenant.
        
        Returns:
            List[str]: List of subscription IDs that match the target list
        """
        try:
            found_subscriptions = []
            all_subscriptions = {}
            
            # Get all available subscriptions
            for subscription in self.subscription_client.subscriptions.list():
                if subscription.state == "Enabled":
                    all_subscriptions[subscription.display_name] = subscription.subscription_id
                    all_subscriptions[subscription.subscription_id] = subscription.subscription_id
            
            print("Available enabled subscriptions:")
            for name, sub_id in all_subscriptions.items():
                if name != sub_id:  # Only show display names, not IDs twice
                    print(f"  - {name} ({sub_id})")
            
            # Find matching subscriptions from target list
            for target_sub in self.target_subscriptions:
                if target_sub in all_subscriptions:
                    found_subscriptions.append(all_subscriptions[target_sub])
                    print(f"✓ Found target subscription: {target_sub}")
                else:
                    print(f"✗ Target subscription not found or not enabled: {target_sub}")
            
            if not found_subscriptions:
                print("Warning: No target subscriptions found!")
                
            return found_subscriptions
            
        except Exception as e:
            print(f"Error getting subscriptions: {e}")
            return []

    def get_resources_from_subscription(self, subscription_id: str) -> List[Dict]:
        """
        Get all resources from a specific subscription.
        
        Args:
            subscription_id (str): The subscription ID
            
        Returns:
            List[Dict]: List of resource information
        """
        try:
            resource_client = ResourceManagementClient(self.credential, subscription_id)
            resources = []
            
            print(f"Scanning subscription {subscription_id}...")
            
            for resource in resource_client.resources.list():
                resources.append({
                    'type': resource.type,
                    'name': resource.name,
                    'location': resource.location,
                    'resource_group': resource.id.split('/')[4] if len(resource.id.split('/')) > 4 else 'Unknown',
                    'subscription_id': subscription_id
                })
            
            print(f"Found {len(resources)} resources in subscription {subscription_id}")
            return resources
            
        except Exception as e:
            print(f"Error getting resources from subscription {subscription_id}: {e}")
            return []

    def get_all_resources(self) -> List[Dict]:
        """
        Get all resources from specified subscriptions only.
        
        Returns:
            List[Dict]: Combined list of all resources from target subscriptions
        """
        all_resources = []
        subscriptions = self.get_subscriptions()
        
        if not subscriptions:
            print("No target subscriptions found to scan.")
            return []
        
        print(f"\nScanning {len(subscriptions)} target subscription(s)...")
        
        for subscription_id in subscriptions:
            resources = self.get_resources_from_subscription(subscription_id)
            all_resources.extend(resources)
        
        return all_resources

    def get_resource_type_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions for common Azure resource types.
        
        Returns:
            Dict[str, str]: Dictionary mapping resource types to descriptions
        """
        return {
            'Microsoft.Compute/virtualMachines': 'Virtual machines for running applications and workloads',
            'Microsoft.Storage/storageAccounts': 'Storage accounts for data storage and file sharing',
            'Microsoft.Web/sites': 'App Service web applications and APIs',
            'Microsoft.Sql/servers': 'Azure SQL Database servers',
            'Microsoft.Sql/servers/databases': 'Azure SQL databases',
            'Microsoft.Network/virtualNetworks': 'Virtual networks for network isolation',
            'Microsoft.Network/networkSecurityGroups': 'Network security groups for traffic filtering',
            'Microsoft.Network/publicIPAddresses': 'Public IP addresses for internet connectivity',
            'Microsoft.Network/loadBalancers': 'Load balancers for distributing traffic',
            'Microsoft.Network/networkInterfaces': 'Network interfaces for VM connectivity',
            'Microsoft.KeyVault/vaults': 'Key vaults for secrets and certificate management',
            'Microsoft.Insights/components': 'Application Insights for application monitoring',
            'Microsoft.Authorization/roleAssignments': 'Role assignments for access control',
            'Microsoft.Resources/resourceGroups': 'Resource groups for organizing resources',
            'Microsoft.ContainerRegistry/registries': 'Container registries for Docker images',
            'Microsoft.ContainerService/managedClusters': 'Azure Kubernetes Service clusters',
            'Microsoft.ServiceBus/namespaces': 'Service Bus namespaces for messaging',
            'Microsoft.EventHub/namespaces': 'Event Hub namespaces for event streaming',
            'Microsoft.Logic/workflows': 'Logic Apps for workflow automation',
            'Microsoft.Web/serverfarms': 'App Service plans for hosting web apps',
            'Microsoft.CognitiveServices/accounts': 'Cognitive Services for AI capabilities',
            'Microsoft.MachineLearningServices/workspaces': 'Machine Learning workspaces',
            'Microsoft.DocumentDB/databaseAccounts': 'Cosmos DB database accounts',
            'Microsoft.Cache/Redis': 'Azure Cache for Redis',
            'Microsoft.ApiManagement/service': 'API Management services',
            'Microsoft.DataFactory/factories': 'Data Factory for data integration',
            'Microsoft.StreamAnalytics/streamingjobs': 'Stream Analytics for real-time analytics',
            'Microsoft.Automation/automationAccounts': 'Automation accounts for runbooks',
            'Microsoft.RecoveryServices/vaults': 'Recovery Services vaults for backup',
            'Microsoft.Network/applicationGateways': 'Application gateways for web traffic management',
            'Microsoft.OperationalInsights/workspaces': 'Log Analytics workspaces for monitoring and logging',
            'Microsoft.Security/automations': 'Security Center automation rules',
            'Microsoft.ManagedIdentity/userAssignedIdentities': 'User-assigned managed identities',
            'Microsoft.AlertsManagement/actionRules': 'Action rules for alert management',
            'Microsoft.Monitor/actionGroups': 'Action groups for alert notifications'
        }

    def analyze_resource_types(self, resources: List[Dict]) -> Dict:
        """
        Analyze resource types and group them by count.
        
        Args:
            resources (List[Dict]): List of resources
            
        Returns:
            Dict: Analysis results with counts and descriptions
        """
        if not resources:
            return {
                'total_resources': 0,
                'resource_types': {},
                'top_locations': {},
                'top_resource_groups': {},
                'subscriptions_scanned': self.target_subscriptions
            }
        
        # Count resources by type
        resource_type_counts = Counter([resource['type'] for resource in resources])
        
        # Group by location
        location_counts = Counter([resource['location'] for resource in resources])
        
        # Group by resource group
        rg_counts = Counter([resource['resource_group'] for resource in resources])
        
        # Group by subscription
        subscription_counts = Counter([resource['subscription_id'] for resource in resources])
        
        # Get descriptions
        descriptions = self.get_resource_type_descriptions()
        
        # Prepare analysis results
        analysis = {
            'total_resources': len(resources),
            'resource_types': {},
            'top_locations': dict(location_counts.most_common(10)),
            'top_resource_groups': dict(rg_counts.most_common(10)),
            'subscription_distribution': dict(subscription_counts.items()),
            'subscriptions_scanned': self.target_subscriptions
        }
        
        # Add resource type details with descriptions
        for resource_type, count in resource_type_counts.most_common():
            analysis['resource_types'][resource_type] = {
                'count': count,
                'description': descriptions.get(resource_type, 'No description available'),
                'percentage': round((count / len(resources)) * 100, 2)
            }
        
        return analysis

    def generate_report(self, analysis: Dict) -> str:
        """
        Generate a formatted report of the analysis.
        
        Args:
            analysis (Dict): Analysis results
            
        Returns:
            str: Formatted report
        """
        report = []
        report.append("=" * 80)
        report.append("AZURE RESOURCE TYPE ANALYSIS REPORT")
        report.append("TARGET SUBSCRIPTIONS: " + ", ".join(analysis.get('subscriptions_scanned', [])))
        report.append("=" * 80)
        report.append(f"Total Resources: {analysis['total_resources']}")
        report.append(f"Unique Resource Types: {len(analysis['resource_types'])}")
        report.append("")
        
        # Subscription distribution
        if analysis.get('subscription_distribution'):
            report.append("SUBSCRIPTION DISTRIBUTION:")
            report.append("-" * 30)
            for sub_id, count in analysis['subscription_distribution'].items():
                report.append(f"  {sub_id}: {count} resources")
            report.append("")
        
        # Resource types section
        report.append("RESOURCE TYPES BY COUNT:")
        report.append("-" * 50)
        for resource_type, details in analysis['resource_types'].items():
            report.append(f"\n{resource_type}")
            report.append(f"  Count: {details['count']} ({details['percentage']}%)")
            report.append(f"  Description: {details['description']}")
        
        # Top locations
        if analysis['top_locations']:
            report.append("\n" + "=" * 50)
            report.append("TOP LOCATIONS:")
            report.append("-" * 20)
            for location, count in analysis['top_locations'].items():
                report.append(f"  {location}: {count} resources")
        
        # Top resource groups
        if analysis['top_resource_groups']:
            report.append("\n" + "=" * 50)
            report.append("TOP RESOURCE GROUPS:")
            report.append("-" * 22)
            for rg, count in analysis['top_resource_groups'].items():
                report.append(f"  {rg}: {count} resources")
        
        return "\n".join(report)

    def save_results(self, analysis: Dict, filename: str = "azure_resource_analysis.json"):
        """
        Save analysis results to a JSON file.
        
        Args:
            analysis (Dict): Analysis results
            filename (str): Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            print(f"Analysis results saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    """
    Main function to run the Azure resource type analysis for specific subscriptions.
    """
    # Define target subscriptions
    target_subscriptions = [
        "ESS-PROD-C00-001",
        "SLProd", 
        "SLSharedDR",
        "SLSharedProd"
    ]
    
    try:
        print("Starting Azure Resource Type Analysis...")
        print(f"Target subscriptions: {', '.join(target_subscriptions)}")
        print("Note: Ensure you're authenticated with Azure CLI or have appropriate credentials configured.")
        print("-" * 80)
        
        # Initialize analyzer with target subscriptions
        analyzer = AzureResourceTypeAnalyzer(target_subscriptions)
        
        # Get all resources from target subscriptions
        print("Collecting resources from target subscriptions...")
        all_resources = analyzer.get_all_resources()
        
        if not all_resources:
            print("No resources found in target subscriptions or unable to access resources.")
            return
        
        # Analyze resources
        print("Analyzing resource types...")
        analysis = analyzer.analyze_resource_types(all_resources)
        
        # Generate and display report
        report = analyzer.generate_report(analysis)
        print("\n" + report)
        
        # Save results
        analyzer.save_results(analysis, "azure_resource_analysis_target_subs.json")
        
        print(f"\nAnalysis complete! Processed {analysis['total_resources']} resources from target subscriptions.")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        print("Please ensure you have:")
        print("1. Azure CLI installed and logged in (az login)")
        print("2. Appropriate permissions to read resources in target subscriptions")
        print("3. Required Python packages installed:")
        print("   pip install azure-identity azure-mgmt-resource azure-mgmt-subscription")

if __name__ == "__main__":
    main()