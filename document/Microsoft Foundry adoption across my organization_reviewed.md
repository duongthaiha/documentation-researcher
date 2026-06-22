**Microsoft Foundry adoption across your organization**

Written by Alex Ruiz, Ayan Banerjee, Chris Tava

This guide presents options for planning adoption of Microsoft Foundry across your organization. It is important to define your target use cases and design your Foundry architecture accordingly.

The focus of this article is to assist customers in adopting Foundry for development purposes for the first time; there is a separate article targeted at production rollouts for agents and models created inside of Foundry.

**Prerequisites**

Before you begin adoption planning, confirm that you have:

- A target Azure subscription(s) and resource group(s) strategy for development and testing environments. This article does not cover production, which is tackled in its own separate article.
- Microsoft Entra ID groups (or equivalent identity groups) should be defined for administrators, project managers, and project users to ensure role-based access governance.
- Reviewed your data residency constraints and identified an initial region plan based on model and feature availability. Certain industries, such as healthcare or financial services, have strict compliance requirements for where data must reside and/or be processed. For details, see [feature availability across cloud regions](https://learn.microsoft.com/en-us/azure/foundry/reference/region-support), our [model deployment guide](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/deployment-types), and our [data processing & privacy article](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy?tabs=azure-portal).
- Reviewed your organization’s security requirements for private networking, encryption, cloud access, and data isolation. It is recommended that your security teams are a part of Foundry adoption planning efforts.
- Familiarized yourself with the concepts of the [agent development lifecycle](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/development-lifecycle) for Microsoft Foundry.

**How are customers adopting Foundry? What are they using it for?**

Across our customers, when it comes to artificial intelligence, we see two main adoptions across enterprises: Generative AI software-as-a-service tools (i.e. Copilot Studio) and customizable, enterprise-wide, cloud-based AI platforms (i.e. Microsoft Foundry).

Some customers want their users to create and consume agents in an easy-to-use tool, and CoPilot Studio squarely fits this need. Other customers lean more to the pro-code developer approach or have compliance or security restrictions that require more control and configurability over agentic development, and so they lean more on Microsoft Foundry.

These approaches tend to coexist, as organizations aim to leverage the full breadth of their employees’ capabilities while making AI widely accessible across the enterprise (we’ll explore the enterprise-wide AI platform later in this article).

In development scenarios, we are seeing Foundry primarily tackle 3 use cases:

1. **Playground-based experimentation:** first-time developers leverage the Playgrounds experience in Foundry to try out different models, prompts, and evaluations in the ideation phase of development.
2. **Model API Hosting:** seasoned developers feel more at home in their IDE of choice, and so platform administrators may provide policy-compliant model endpoints for developers to consume as they please.
3. **End-to-end AI pipelines:** developers may choose to build complete solutions with Foundry that take advantage of models, agents, evaluations tools, and content safety features.

The content of this article is geared toward (1) & (2), with a more robust article around complete production rollouts available elsewhere.

|  |
| --- |
| **TIP:** We highly recommend familiarizing yourself with the [agent development lifecycle in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/development-lifecycle) *before* proceeding with the remainder of the article. Concepts from the lifecycle will be addressed in later sections of the article when we cover observability, governance, and monitoring. |

**Microsoft Foundry adoption checklist**

Many customers find it useful to have an adoption checklist handy that outlines the important components of adopting a new technology platform. We’ve provided an adoption checklist below for you to use as a starting point:

|  |  |
| --- | --- |
|  | Define your environment boundaries across development, testing, and production. |
|  | Identify or assign ownership for each Foundry resource and project scope. Leverage the approaches to organizing Foundry section of this article to determine how your organization will adopt Foundry. |
|  | Identify any resource connection requirements for your Foundry projects. |
|  | Define your network configuration for Foundry based on the three recommended patterns presented in this article. Leverage infrastructure-as-code templates wherever possible. |
|  | Determine whether customer-managed keys are required by policy. This is an important consideration for highly regulated industries such as healthcare. |
|  | Define a model deployment strategy to ensure model capacity and that your organization remains compliant with any data residency or processing requirements. |
|  | Identify environment-wide policies that are required to apply to model and agent deployments – i.e. token and rate limit policies via APIM, Foundry guardrails, Azure Policies restricting certain model usage, etc. |
|  | Define role-based access control assignments for platform administrators, project managers, and project users. Root your assignments in the Microsoft best practice of least-privilege. |
|  | Determine your cost management strategy for tracking costs associated with Foundry, such as model, agent, and tool calling, or associate resources. |
|  | Enable monitoring capabilities to capture information related to your Foundry environment and the agents created there. |
|  | <!-- Added based on ENGINEERING review --> Define your source control and CI/CD operating model for Foundry, including what is promoted via IaC versus SDK/REST automation, and how rollback will work for prompts, agents, model mappings, tools, and knowledge artifacts. |
|  | <!-- Added based on ENGINEERING review --> Define a drift-management policy for portal edits in development, test, and production-like environments. |
|  | <!-- Added based on ENGINEERING review --> Define a minimum telemetry baseline and release gates for agent changes before any workload is considered ready to move from development into broader testing or production rollout. |

We’ll start with the considerations to keep in mind for organizing projects inside Microsoft Foundry.

**Project setup considerations for adopting Foundry**

**What are Foundry Projects?**

Microsoft Foundry uses a Foundry account resource and Foundry project distinction for resource organization – like a parent / child relationship. The Foundry account resource provides the shared control plane, governance, and core AI capabilities such as models, services, and management for all associated Foundry projects. Foundry projects are designed to represent specific use cases for developers to work on. They’re containers to organize components such as agents or files for an application. While they inherit security settings from their parent Foundry resource, they can also implement their own access controls, resource connections, and other governance controls.

You can have many Foundry projects within a Foundry resource, as seen below:

![](Microsoft Foundry adoption across my organization_images/image1.png)

**Approaches to organizing Foundry**

There are two perspectives to consider when approaching Foundry adoption: the enterprise-wide perspective and the department-level perspective.

**The “Enterprise-Wide” Perspective**

Many organizations gravitate towards viewing Foundry as their next generation AI platform, and leaders will naturally want to build a single, enterprise-wide AI platform around Foundry.

|  |
| --- |
| **TIP:** It is crucial to view Foundry as a *development* platform, not a *consumption* platform. It is acceptable and, in some cases, encouraged to pursue an enterprise-wide AI platform, where many users can log on and consume models and agents from one secure application. |

When tasked with an enterprise-wide adoption of Foundry, you will want to urge decision makers towards segmenting Foundry deployments across logical boundaries such as data domains or business units to ensure developer autonomy. See an example below:

![](Microsoft Foundry adoption across my organization_images/image2.png)

To fulfill this “enterprise-wide” vision, you will have:

- **Department-level development environments:** Many Foundry resources, each for your different departments to use for development purposes,
- **Source Control & DevOps:** a process by which to check-in and promote your agentic code, or deploy your created agents across your development, test, and production environments,
- **API Governance:** a governance layer using Azure API Management, where rate limiting and token limit policies are applied to your models and agents APIs to control usage and costs.
- **Consumption Platform:** an application layer where users can consume your agents or models – such as CoPilot Studio, or your own custom application where you expose deployed models and agents.

<!-- Added based on ENGINEERING review -->
For engineering-led rollouts, we recommend a two-layer promotion model:

1. **Platform / control-plane promotion:** provision and update Foundry accounts, projects, networking, RBAC, diagnostic settings, APIM / AI Gateway, model deployments, and dependent Azure resources using IaC such as Bicep or Terraform, optionally orchestrated with [`azd`](https://learn.microsoft.com/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension).
2. **Agent application / data-plane promotion:** version prompts, agent definitions, tool or MCP contracts, evaluation datasets, and policy files in Git, then deploy and update agents, versions, evaluations, and other project-scoped artifacts through SDK, REST, CLI, or `azd` post-provision automation.

This distinction is important because not every Foundry-related artifact is a first-class ARM resource. For example, Foundry IQ knowledge sources and knowledge bases are data-plane objects and should be created or updated through post-provision SDK/REST automation rather than ARM/Bicep. See [Deploy an agent to Microsoft Foundry with the Azure Developer CLI AI agent extension](https://learn.microsoft.com/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension), [Add a new connection to your project](https://learn.microsoft.com/azure/foundry/how-to/connections-add), and local implementation notes referenced during the ENGINEERING review.

**The “Department-level” Perspective**

Let’s double click into the department-level approach to organizing Foundry. We’ve seen that organizations want to enable their departments or business groups to take advantage of emerging AI technologies such as agents to deliver impact by solving real business problems.

These developers need an environment where they can test models, build agents, and implement evaluations – either programmatically, or through a GUI – with a certain level of autonomy. Developer teams may need to access sensitive, department-level data or track costs specific to their budget; it is for this reason that we recommend segmenting your Foundry resources across these department-level boundaries, as seen below:

![](Microsoft Foundry adoption across my organization_images/image3.png)

In this approach, you’ll give developers or developer teams their own projects inside of their respective Foundry resource and leverage shared connected resources – like storage and search indexes – across all those projects. This way, you’re keeping development scoped at the department-level, while still consolidating costs and maintaining a degree of collaboration.

|  |
| --- |
| **TIP:** You may be asking, “How many model deployments should I have inside each Foundry resource?”, “Is it recommended that users share model deployments?”, or “Should I give each user their own model deployment?” The answer here depends on your cost management/tracking requirements. |

<!-- Added based on ENGINEERING review -->
For engineering organizations planning to promote workloads beyond experimentation, it is helpful to distinguish between:

- **Exploration environments:** shared, lower-cost, experimentation-focused Foundry resources with multiple projects.
- **Promotable dev/test environments:** environment-specific resources and projects that preserve the same deployment model, logical naming, observability, and governance patterns you intend to carry into production.
- **UAT / pre-production environments:** the closest non-production mirror of production in terms of networking, connections, authentication, quotas, and monitoring.

This preserves environment parity without requiring identical spend. In practice, teams should keep the same topology pattern, deployment pipeline shape, aliasing strategy, and observability contract across environments, while scaling down quotas, SKUs, corpus size, and capacity where appropriate. See [Foundry planning](https://learn.microsoft.com/azure/foundry/concepts/planning) and [Foundry architecture](https://learn.microsoft.com/azure/foundry/concepts/architecture).

**Department-level Enclaves**

We recognize that in some more restricted industries, such as healthcare or financial services, there are stricter requirements over the sensitivity and handling of data; these industries require more segmentation and more granular control over Foundry, and so we introduce the concept of the “department-level enclave”:

![](Microsoft Foundry adoption across my organization_images/image4.png)

Here, each project receives their own respective resources, and users are *strictly* given role-based access to only their project and its supporting resources.

This approach involves trade-offs between compliance and operational complexity. While it enables greater resource segmentation and supports the governance of sensitive use cases with appropriate safeguards, it also increases environmental complexity and associated costs. There are also limitations to be aware of, [such as private endpoint sharing rules or maximum connections per project](https://learn.microsoft.com/en-us/azure/foundry/how-to/connections-add?tabs=foundry-portal), that are important to understand.

|  |
| --- |
| **TIP:** When it comes to setting up an enclave, carefully consider each use case before you create a new project. Ask questions such as:   - What kind of data will this project require? - Will de-identified data suffice? If not, does the data need to be stored separately? - Will indexed data need to be treated similarly? - Does this use case require robust logging and security of conversation threads?   If yes, then you may benefit from the enclave scenario. You may find that some resources can be shared, while others may not. |

A key piece of the department-level approach is defining your organization’s model strategy. Certain models are only available in certain regions and in certain deployment configurations, which can impact where data is processed. It is important to understand model availability as well as model deployment configurations and plan accordingly. We will cover that later in this article.

**Securing your Foundry environment**

There are 3 primary ways to configure network security for your Foundry environment: *public*, *private*, and *hybrid*. The following section outlines each of these configurations and provides the underlying rationale, as well as infrastructure-as-code templates you can use to get started with your deployment.

|  |
| --- |
| **NOTE:** All of these configurations are variations of the [Standard Agent Setup](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/standard-agent-setup). If you are looking for a quick, easy-to-deploy Foundry configuration where all underlying components are managed by Microsoft, please see the basic agent setup. |

The decision matrix below can help orient you towards which environment configuration is appropriate for your organization:

Deployment 1 – Standard Agent Setup (Public)

The public standard agent setup is the recommended configuration for customers looking for a complete Foundry deployment that includes all its ancillary Azure services but aren’t restricted by a requirement to deploy an environment with private networking.

![](Microsoft Foundry adoption across my organization_images/image5.png)

With this deployment configuration, you’ll get the following resources deployed into your resource group:

- **Microsoft Foundry account & project:** parent resource and one project in which to work in by default.
- [**Foundry project capability host**](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/capability-hosts)**:** this sub-resource allows you to bring your own Azure resources and specifies resources for storing agent states such as conversation history, file uploads, and vector stores.
- **Azure Cosmos DB:** stores conversation history and threads.
- **Azure Storage:** stores data or files produced by your Agents, models, or Speech and Language services.
- **Azure AI Search:** stores embeddings and vector data.
- **Azure Key Vault:** stores encrypted keys that are used to connect across resources or APIs.

You can find an infrastructure-as-code template for this deployment configuration here: [*foundry-samples/infrastructure/infrastructure-setup-bicep/41-standard-agent-setup at main · microsoft-foundry/foundry-samples*](https://github.com/microsoft-foundry/foundry-samples/tree/main/infrastructure/infrastructure-setup-bicep/41-standard-agent-setup)

|  |
| --- |
| **NOTE:** You have the option to point the template to existing resources or have the template create new ones. In either case, these dependencies are customer-managed resources, not Microsoft-managed resources (as is the case in the basic agent setup). |

Deployment 2 – Standard Agent Setup (Private)

The private standard agent setup includes everything that the public standard agent setup includes, however all the resources are deployed in your own virtual network alongside private endpoints for each of the respective Azure resources. For customers in regulated industries such as healthcare or financial services, this is generally the recommended approach for deploying Foundry. There’s a more detailed article around setting up this environment found [here](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/virtual-networks).

|  |
| --- |
| **NOTE:** There is also support for a variation of this deployment but with a Microsoft-managed VNET, you can read more about that [here](https://learn.microsoft.com/en-us/azure/foundry/how-to/managed-virtual-network). |

![Diagram of the recommended network isolation for Foundry.](Microsoft Foundry adoption across my organization_images/image6.png)

An important callout for this private setup is the introduction of the Agents subnet – also called the delegated subnet – where your agents are deployed into. Although you may bring your own Azure resources, deployed agents (also called prompt-based agents) always get deployed into this subnet onto Microsoft-managed container applications where the agent runtimes are hosted. Two key points:

- Those container applications exist inside of the delegated subnet and are not seen or managed by customers.
- Customers are not charged for those container applications but are charged for the calls made to agents that run on those containers.

You can find a deployment template for this configuration here: [*foundry-samples/infrastructure/infrastructure-setup-bicep/15-private-network-standard-agent-setup at main · microsoft-foundry/foundry-samples*](https://github.com/microsoft-foundry/foundry-samples/tree/main/infrastructure/infrastructure-setup-bicep/15-private-network-standard-agent-setup)

There is also a modified version of this template that supports customer-managed keys.

|  |
| --- |
| **NOTE:** As agentic platform capabilities continue to mature, we are seeing customers move towards including Azure API Management as a core component of their Foundry deployments to manage model and agent APIs via policies. While there is a [deployment template of this private standard agent setup that includes APIM](https://github.com/microsoft-foundry/foundry-samples/tree/main/infrastructure/infrastructure-setup-bicep/16-private-network-standard-agent-apim-setup-preview), there are efforts underway to integrate APIM and Foundry via the [AI Gateway feature](https://learn.microsoft.com/en-us/azure/foundry/configuration/enable-ai-api-management-gateway-portal) (currently in public preview). |

Deployment 3 – Standard Agent Setup (Hybrid)

Lastly, there is one more deployment configuration for Foundry that is not often seen, but deserves mention: the hybrid configuration. The key differentiator with this configuration is the ability to switch between public and private Foundry access. Organizations will want to use this deployment configuration when they want:

- **Private backend resources:** Keep Azure AI Search, Cosmos DB, and Azure Storage behind private endpoints.
- **MCP Server integration:** Deploy MCP servers on the VNET that agents can access via a data proxy.
- **Private Foundry:** Full network isolation with secure access via VPN, ExpressRoute, or Bastion.
- **Optional public Foundry access:** Switch to public access for portal-based development if allowed by your organization’s security policy.

Organizations will want to avoid this configuration and defer to Deployment 2 – Standard Agent Setup (private) when they need:

- **Fully managed private networking:** Including managed VNET with Microsoft-managed private endpoints.
- **Compliance requirements:** Regulations that require a different private networking topology.

Below is a table that compares private deployment and hybrid deployments:

|  |  |  |  |
| --- | --- | --- | --- |
| Deployment 2 (Private) vs. Deployment 3 (Hybrid) | | | |
| Feature | Private | Hybrid – “Private” | Hybrid – “Public” |
| AI Services public access | Disabled | Disabled | Enabled |
| Foundry Portal access | Via VPN, ExpressRoute, or Bastion | Via VPN, ExpressRoute, or Bastion | Works directly |
| Backend resources | Private | Private | Private |
| Data Proxy | Configured | Configured | Configured |
| Secure connection required | Yes | Yes | No |

You can find a deployment template for this configuration here: [*foundry-samples/infrastructure/infrastructure-setup-bicep/19-hybrid-private-resources-agent-setup at main · microsoft-foundry/foundry-samples*](https://github.com/microsoft-foundry/foundry-samples/tree/main/infrastructure/infrastructure-setup-bicep/19-hybrid-private-resources-agent-setup)

Define your model strategy

In a constantly evolving space like AI, it is important for an organization to define its model strategy. Model lifecycle stages or regional capacity constraints can affect the models you choose to integrate into your applications. A viable model strategy should address three key areas:

1. **Model lifecycle:** models are continuously refreshed with newer, more capable models. As a part of this process, model providers may deprecate and retire older models, requiring application updates to use newer model versions. It is important to understand the model lifecycle stages, and how [Foundry models](https://learn.microsoft.com/en-us/azure/foundry/concepts/model-lifecycle-retirement) and [Azure Open AI models](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirements?tabs=text) are deprecated and retired.
2. **Deployment types:** There are different [deployment offerings](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types), which impact where your prompt inputs are processed geographically. For customers in regulated industries, there may be a requirement for [data processing](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy?tabs=azure-portal) to occur within a geographical region.
3. **Region availability:** Along the same lines as deployment types, it is important when selecting a model to verify which regions are supported for the model your team may be evaluating. Regional support can vary depending on available capacity, and not all models get rolled out to all regions.

<!-- Added based on ENGINEERING review -->
For engineering teams, a practical model strategy should also define **how model changes are promoted and rolled back**. We recommend using **logical model aliases** in application configuration (for example, `chat-primary`, `reasoning-secondary`, or `judge-model`) and managing the environment-specific mapping of those aliases to actual deployments through source control and pipeline promotion. This allows teams to change capacity, patch versions, or deployment targets without hardcoding model endpoints in application code.

When model behavior changes are material—such as a model family change, a region change, or a meaningful latency/cost profile change—prefer releasing a **new agent version** that references the new model mapping and validating it with evaluations before shifting traffic. For lower-risk changes such as approved capacity moves, teams may update the alias mapping directly through controlled deployment automation. In both cases, rollback should be explicit: revert the alias mapping or route traffic back to the previous agent version. See [model lifecycle retirement](https://learn.microsoft.com/en-us/azure/foundry/concepts/model-lifecycle-retirement), [deployment types](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types), and [Manage hosted agents](https://learn.microsoft.com/azure/foundry/agents/how-to/manage-hosted-agent).

Planning your user access strategy for Foundry

<!-- Added based on ENGINEERING review -->
A practical Foundry user access strategy should separate **human access** from **runtime access** and apply least-privilege at the lowest reasonable scope.

We recommend the following baseline role model:

- **Platform administrators:** a small set of centrally managed operators with access at the Foundry account or resource scope, plus any required privileges for networking, APIM, monitoring, and dependent Azure resources.
- **Project managers / delegated administrators:** project-scoped users who can manage project-level access and developer workflows without receiving broad subscription- or resource-group-level rights.
- **Developers / agent builders:** project-scoped users with the minimum rights necessary to build, test, and evaluate inside their project.
- **Runtime identities:** managed identities used by agents, pipelines, APIM, and other automation. These should never be replaced by broad human or shared service credentials.
- **Consumers:** users of downstream applications or APIs rather than users with direct Foundry administration permissions.

Microsoft provides Foundry-specific roles such as [Foundry User, Foundry Project Manager, and Foundry Owner / Foundry Account Owner](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry), and Azure built-in roles for AI and machine learning scenarios are documented [here](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles/ai-machine-learning).

<!-- Added based on ENGINEERING review -->
As a best practice:

- Assign **platform-level roles** only to central operations groups, ideally through Privileged Identity Management (PIM) or just-in-time elevation.
- Assign **developer roles** at the **project scope**, not at subscription or resource group scope, unless a specific Azure resource requires separate access.
- Grant **resource-specific roles** on connected services only to the identities that require them—for example Storage Blob Data Reader/Contributor, Search Index Data Reader/Contributor, Cosmos DB data roles, Key Vault Secrets User, or Log Analytics Reader.
- Use **Microsoft Entra groups** as the principal assignment target wherever possible.

<!-- Added based on ENGINEERING review -->
We also recommend a **secretless-by-default** operating model:

- Use workload identity federation for CI/CD systems such as GitHub Actions or Azure DevOps.
- Use managed identity for Hosted agents and other runtimes to access downstream Azure resources.
- Use managed identity for APIM where it calls Azure OpenAI, Foundry, Content Safety, or other Azure backends.
- Only use secrets where the downstream system cannot authenticate with Microsoft Entra ID; if unavoidable, store them in Key Vault and inject them at deployment or runtime rather than storing them in code or repositories.

This aligns with [`azd` guidance for Foundry](https://learn.microsoft.com/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension) and the managed identity guidance exposed in [Manage hosted agents](https://learn.microsoft.com/azure/foundry/agents/how-to/manage-hosted-agent).

Adopting a cost management strategy in Foundry

<!-- Added based on ENGINEERING review -->
For engineering teams, the most effective cost strategy is to make the **Foundry project the primary ownership and reporting boundary**, then enrich that with tags, telemetry, quotas, and gateway policies for finer attribution.

We recommend:

- Using one project per product, use case, or team boundary where cost ownership differs.
- Tagging all deployable resources with consistent metadata such as `costCenter`, `department`, `project`, `agentName`, `environment`, `owner`, and `releaseVersion`.
- Emitting per-request telemetry that records agent name/version, model deployment name, prompt version, token usage, tool usage, latency, and success/failure status.

<!-- Added based on ENGINEERING review -->
At minimum, teams should measure:

- prompt tokens
- completion tokens
- total tokens
- estimated token cost
- tool-call count and duration
- retrieval/query cost contribution where applicable
- evaluation costs
- latency and retry overhead
- error and throttling rates

Foundry observability provides token, latency, error, and quality visibility, and APIM AI Gateway provides token governance and policy support. See [Foundry observability](https://learn.microsoft.com/azure/foundry/concepts/observability), [Enforce token limits for models](https://learn.microsoft.com/azure/foundry/control-plane/how-to-enforce-limits-models), and [APIM AI gateway policies](https://learn.microsoft.com/azure/api-management/api-management-policies#ai-gateway).

<!-- Added based on ENGINEERING review -->
A practical cost-control baseline includes:

1. **Per-project token quotas and TPM caps** using AI Gateway / APIM where applicable.
2. **Environment-specific quota envelopes**—lower for dev, moderate for test/UAT, and approved capacity for production.
3. **Budget alerts and anomaly detection** at subscription, resource group, tag, or project level.
4. **Scheduled cleanup** for stale non-production assets, obsolete agent versions, and dormant experimental resources.
5. **Optional semantic caching** only where correctness and compliance allow.

Where model deployments are shared across teams, adopt a layered quota model:
- **Tier 1:** Azure model capacity planning by model, region, and deployment type.
- **Tier 2:** project-level quotas via Foundry AI Gateway or APIM.
- **Tier 3:** application- or client-level quotas via APIM subscriptions, products, or policy.

Governance & monitoring strategy in Foundry

While the scope of this guide is limited to development workloads (and not production), we recognize the need for platform governance and monitoring strategies in development environments. Platform administrators may want to:

- Govern API endpoints for models or agents in development,
- Control access to certain models available in the Foundry catalog,
- Monitor usage or operations of agents deployed for testing in dev / test / UAT environments,
- Verify that logging configurations satisfy organizational requirements.

The list above may not be exhaustive but is a well-rounded set of asks that we commonly see customers looking for guidance around. We’ve gathered information around these four areas, which you can find below.

Model & Agentic API Governance via an AI Gateway

<!-- Added based on ENGINEERING review -->
For engineering-led Foundry adoption, we recommend treating **Azure API Management (APIM)** or the **Foundry AI Gateway** as the policy enforcement plane for model and agent APIs, with all gateway configuration stored in source control and promoted through environments just like application code.

At a minimum, place the following artifacts under version control:

- APIM instance or workspace configuration
- APIs, products, backends, and subscriptions
- policy XML and policy fragments
- named value references and environment overlays
- test assertions for policy behavior

See [Enable AI Gateway in Foundry](https://learn.microsoft.com/azure/foundry/configuration/enable-ai-api-management-gateway-portal), [AI gateway capabilities in APIM](https://learn.microsoft.com/azure/api-management/genai-gateway-capabilities), and the [APIM AI gateway policy reference](https://learn.microsoft.com/azure/api-management/api-management-policies#ai-gateway).

<!-- Added based on ENGINEERING review -->
A recommended baseline policy set for model and agent APIs includes:

1. **Authentication and authorization** using Microsoft Entra ID or managed identity where possible.
2. **Token limits and quotas** using AI gateway token policies.
3. **Token metric emission** for chargeback and monitoring.
4. **Content safety checks** where appropriate.
5. **Rate limiting and concurrency controls.**
6. **Retry and circuit-breaker behavior** for resilient backend access.
7. **Backend routing and failover** when multiple deployments or regions are used.
8. **Caching** only where the use case tolerates it.
9. **Request/response logging with redaction.**
10. **Header stamping / correlation IDs** to correlate project, agent, version, and environment.

<!-- Added based on ENGINEERING review -->
We recommend the following promotion pattern:

- update gateway policies through pull requests
- lint and validate policies in CI
- deploy to a development APIM environment or workspace
- run policy tests, including quota, safety, authentication, and routing behavior
- promote the same versioned policy package to test and production-like environments

Avoid editing APIM policies directly in production-like environments except as an emergency measure. If a break-glass change is made, reconcile it back into source control immediately.

Control model access with Azure Policy

Certain organizations in more restricted industries may seek to govern or restrict the deployment of specific models in the Microsoft Foundry model catalog. Microsoft provides built-in Azure policies for governing both [model deployments](https://learn.microsoft.com/en-us/azure/foundry/how-to/model-deployment-policy?tabs=cli) as well as [Foundry tools](https://learn.microsoft.com/en-us/azure/ai-services/policy-reference?context=/azure/foundry/context/context) to give customers control over which models and tools developers can use.

|  |
| --- |
| **NOTE:** These Azure Policies *do not* make any UI changes inside of the Microsoft Foundry portal; users will still be able to see model and tool cards in the catalog but will not be able to deploy them. Be sure to communicate to your users that you’ve put policies in place that restrict usage of certain models or tools! |

Monitoring your deployed agents with Foundry’s observability suite

A large part of the agent development cycle focuses on developing agent observability. Observability refers to the ability to monitor, understand, and troubleshoot AI agents throughout their lifecycle. There are three core capabilities that make up the Foundry observability suite:

- 1. **Evaluations:** [Evaluators](https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/evaluate-agent) measure the quality, safety, and reliability of agentic responses throughout development and into production. Different agents may use different evaluators depending on their specific purpose; however, some organizations may require a set of baseline evaluators across all agents – be sure to check with your AI platform or security administrator.
  2. **Monitoring:** Microsoft Foundry provides [real-time dashboards](https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard?tabs=python) for tracking operational metrics, token consumption, latency, error rates, and quality scores. You can set up alerts when outputs fail quality thresholds or produce harmful content. We also provide a [fleet monitoring guide](https://learn.microsoft.com/en-us/azure/foundry/control-plane/monitoring-across-fleet) for platform administrators who are looking to monitor agents across many Foundry resources, as well as a guide for [performing lifecycle operations at scale](https://learn.microsoft.com/en-us/azure/foundry/control-plane/how-to-manage-agents).
  3. **Tracing:** [Tracing](https://learn.microsoft.com/en-us/azure/foundry/observability/concepts/trace-agent-concept) offers insight into the execution flow of agentic systems, particularly into API calls, tool invocations, agentic decisions, and inter-service dependencies. It’s a key piece of troubleshooting or debugging your developers may need to do as they refine their agentic system.
  4. **Guardrails:**

Alongside enablement of these features across all agent development efforts, it is important for developer teams to understand and implement red teaming as a pre-requisite to shipping any agentic system live into production. AI Red Teaming focuses on simulations or testing by both human users and AI Red Teaming agents to uncover security vulnerabilities or probe for novel risks in an agentic system.

|  |
| --- |
| **TIP:** Microsoft has released a guide for developer teams to familiarize themselves not only with red teaming as a concept, but also how to implement red teaming using Microsoft Foundry’s [AI Red Teaming agent](https://learn.microsoft.com/en-us/azure/foundry/concepts/ai-red-teaming-agent). |

<!-- Added based on ENGINEERING review -->
For engineering teams, we recommend defining explicit **release-quality gates** before promoting any meaningful agent change. At a minimum, the following gates should be considered:

1. **Static and configuration validation**
   - validate `agent.yaml` or equivalent agent specifications
   - validate prompt file presence and template structure
   - validate MCP / OpenAPI / tool schemas
   - validate IaC, policy, and configuration packages
   - fail builds if secrets are detected in code or manifests

2. **Unit and component tests**
   - prompt assembly and templating logic
   - tool response parsing
   - fallback and routing logic
   - guardrail helper behavior

3. **Tool / contract tests**
   - request and response schema validation
   - timeout and authorization failure handling
   - malformed payload behavior
   - fallback behavior when tools or retrieval systems are unavailable

4. **Golden dataset regressions**
   - compare current and candidate releases on representative prompts
   - fail on unacceptable regressions in groundedness, relevance, task completion, or tool-use accuracy

5. **Safety and red-team baselines**
   - prompt injection attempts
   - jailbreak attempts
   - system prompt leakage probes
   - data exfiltration attempts
   - unsafe content scenarios

6. **Performance and cost thresholds**
   - P95 latency change
   - token growth per request
   - tool-call count per request
   - dependency failure rate
   - throttling or quota exhaustion

7. **Trace review and, where required, human approval**
   - especially for model-family changes, tool-contract changes, new privileged connectors, or major prompt rewrites

This aligns with [Cloud Adoption Framework guidance on secure AI agent processes](https://learn.microsoft.com/azure/cloud-adoption-framework/ai-agents/build-secure-process#4-agent-observability), [Evaluate your AI agents](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent), and [Monitor agents with the Agent Monitoring Dashboard](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard).

<!-- Added based on ENGINEERING review -->
For Hosted agents specifically, prefer **version-based canary rollout** using agent versioning and traffic routing. A practical progression is to deploy a new version, route a small percentage of traffic to it, verify quality/safety/SLO metrics, then increase traffic gradually. If regression is detected, route traffic back to the previous version immediately. See [Manage hosted agents](https://learn.microsoft.com/azure/foundry/agents/how-to/manage-hosted-agent).

<!-- Added based on ENGINEERING review -->
Teams should also define **artifact-specific change management**:

- **Hosted agent code / image / runtime settings:** create a new Hosted agent version; rollback by routing traffic back.
- **Prompts and system instructions:** treat as versioned application artifacts in Git; avoid portal-only edits in shared environments; rollback by redeploying the prior version or routing to the previous agent version.
- **Model deployment mappings:** manage through source-controlled alias mappings; rollback by restoring the prior mapping or prior agent version.
- **Tool / MCP contracts:** version contracts explicitly and keep prior versions available during rollout.
- **Foundry IQ knowledge definitions and retrieval configuration:** treat as versioned data-plane artifacts managed by post-provision SDK/REST automation; prefer blue/green knowledge base or index version patterns for safe rollback.
- **APIM / AI Gateway policies:** version and promote through pipeline; rollback by redeploying the prior policy package.

Prompt edits or model swaps made directly in the portal should be reserved for break-glass situations and reconciled back into Git immediately.

<!-- Added based on ENGINEERING review -->
A practical **minimum telemetry baseline** for development and test environments should include:

**Request and correlation metadata**
- timestamp
- environment
- service/app name
- agent name
- agent version
- release version or Git SHA
- trace ID and span ID
- conversation ID and thread ID where applicable
- request/run ID
- caller application or pseudonymous user identity

**Model and prompt metadata**
- model deployment name
- model family/version where available
- deployment region
- prompt version or system prompt hash
- tool policy version
- knowledge base or index version
- APIM policy package version
- feature or routing flags

**Tool and retrieval telemetry**
- tool name and contract version
- target endpoint/service
- duration
- success/failure
- status code or exception class
- retry count
- timeout flag
- sanitized input and output summaries
- fallback path

**Cost and reliability telemetry**
- prompt, completion, and total tokens
- estimated cost
- tool-call count
- retrieval call count
- cache hit/miss if applicable
- end-to-end latency
- model latency
- tool latency
- timeout rate
- error rate
- throttling / 429 rate

**Quality and safety telemetry**
- scheduled and continuous evaluation scores
- red-team results
- pass/fail thresholds used for the release
- comparison against the previous release

See [Set up tracing in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup), [Monitor agents with the Agent Monitoring Dashboard](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard), and [Evaluate your AI agents](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent).

<!-- Added based on ENGINEERING review -->
When collecting these signals, implement **redaction rules** up front. Do not log secrets, bearer tokens, connection strings, or raw regulated data unless explicitly approved. Prefer hashed identifiers, field-level masking, truncated arguments, and allowlisted logging for safe fields only.

AI Platform resource usage tracking, audit logging with Azure Monitor & Log Analytics

Administrators want visibility into the health and usage of Microsoft Foundry and other platform-level resources. You’ll want to [configure Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/data-sources) as the common monitoring data platform to monitor Azure resources like Microsoft Foundry, log data from Microsoft Entra ID, and application data – while routing [diagnostic logs](https://learn.microsoft.com/en-us/azure/ai-services/diagnostic-logging?context=/azure/foundry/context/context) to be queried or consumed in Azure Log Analytics.

To support security, compliance, and operational traceability, administrators should explicitly configure audit logging across Microsoft Foundry and dependent platform services. Azure Monitor diagnostic logs form the backbone of this capability.

|  |  |  |
| --- | --- | --- |
| **Area** | **Default state (out of the box)** | **After explicit configuration** |
| **Platform metrics** | ✅ Basic metrics available in Azure Monitor | Optionally route metrics to [**Azure Monitor / Log Analytics**](https://learn.microsoft.com/en-us/azure/azure-monitor/fundamentals/data-sources) for correlation and alerting |
| **Control-plane activity (resource changes)** | ❌ Not collected | ✅ Enable **Diagnostic Settings → Audit logs** via [**Create diagnostic settings**](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/create-diagnostic-settings) |
| **Data-plane activity (API / agent usage)** | ❌ Not collected | ✅ Enable **Request/Response logs** using [**Azure AI services diagnostic logging**](https://learn.microsoft.com/en-us/azure/ai-services/diagnostic-logging) |
| **Audit log coverage** | ❌ No logs emitted (categories exist but inactive) | ✅ Select **Audit / All log categories** per [**Diagnostic settings guidance**](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings) |
| **Identity activity (who performed actions)** | ❌ Not captured with resource logs | ✅ Enable [**Microsoft Entra ID logs**](https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-sign-ins) |
| **Centralized logging / querying** | ❌ No centralized log store | ✅ Route logs to [**Log Analytics workspace**](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs) |
| **Retention / compliance** | ❌ No retention configured | ✅ Configure retention using [**Log Analytics retention**](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure) and export via [**Log export options**](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-data-export) |

Out-of-the-box, Azure provides metrics-only visibility, while all meaningful audit logging (control plane, data plane, and identity) must be explicitly enabled via diagnostic settings and Entra ID logging.

A log retention strategy should align to security, cost, and regulatory requirements. Below are recommendations for retaining different kinds of log data:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| **Category** | **Purpose** | **Default behavior** | **Recommended configuration** | **Supporting guidance** |
| **Log Analytics (hot data)** | Real-time querying, alerting, investigations | ~30 days default retention (varies by table) | Set **30–90 days** for operational monitoring; extend up to **2 years** for security investigations | [Configure Log Analytics retention](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure) |
| **Long-term retention (cold data)** | Compliance, audit history, infrequent access | Not configured | Export logs to **Azure Storage** with lifecycle policies for multi-year retention (e.g., 1–7+ years) | [Log export options](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-data-export) |
| **Tamper protection / immutability** | Prevent log modification or deletion (regulatory requirement) | Not configured | Use **immutable storage (WORM policies)** on Azure Storage for audit logs | [Azure Monitor data export + storage guidance](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-data-export) |
| **SIEM / Security integration** | Centralized threat detection and correlation | Not configured | Stream logs to **Event Hub → SIEM (e.g., Microsoft Sentinel)** | [Create diagnostic settings](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/create-diagnostic-settings) |
| **Retention management model** | Balances cost, performance, compliance | Single-tier (if unmanaged) | Use **tiered model**: Log Analytics (hot) + Storage (cold/archive) | [Azure Monitor retention model](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure) |
| **Cross-region / durability (optional)** | Resilience, regulatory data residency | Not guaranteed | Use **GRS/GZRS storage replication** for archived logs | [Log Analytics export guidance](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/logs-data-export) |

A compliant audit strategy requires tiered retention: short-term logs in Log Analytics for detection and investigation, with long-term, immutable storage for regulatory and audit purposes.

<!-- Added based on ENGINEERING review -->
For engineering teams, we recommend standardizing a minimum **dashboard and alerting baseline** in development and test:

**Dashboards**
1. **Release health dashboard** – requests, success rate, latency percentiles, token usage, version comparisons.
2. **Quality and safety dashboard** – evaluation results, red-team findings, pass/fail status, delta vs previous release.
3. **Dependency and tool dashboard** – per-tool success rate, latency, timeouts, retries, auth failures, fallback rate.
4. **Cost and quota dashboard** – token consumption by agent/version, estimated cost by project, throttle events, quota trends.

**Baseline alerts**
- run success rate below **95%**
- sustained P95 latency above **10 seconds**
- error rate above defined threshold
- 429 / throttling spikes above baseline
- token-per-request growth above budget
- evaluation score drops below release threshold
- critical red-team finding
- loss of expected telemetry after deployment

These values should be tuned by use case, but they provide a strong starting point aligned with Foundry monitoring guidance. See [Monitor agents with the Agent Monitoring Dashboard](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard).

<!-- Added based on ENGINEERING review -->
Teams should also maintain a lightweight **incident-response runbook** for dev/test/UAT environments. At minimum, it should answer:

1. **Detect** – which alert, evaluation, or smoke test failed?
2. **Triage** – which environment, agent version, prompt version, model mapping, tool contract version, and KB/index version are involved?
3. **Stabilize** – can traffic be routed back, a prior model alias restored, a tool disabled, or a prior knowledge/index version reactivated?
4. **Investigate** – which traces, conversation IDs, dependency spans, and recent releases explain the regression?
5. **Correct** – what change will be made through PR and CI/CD?
6. **Review** – what test, threshold, or documentation update prevents recurrence?

<!-- Added based on ENGINEERING review -->
Finally, define an explicit **authoritative deployment surface and drift policy** for your platform:

- Treat **ARM/Bicep/Terraform** as authoritative for Foundry accounts, projects, model deployments, connections, networking, RBAC, diagnostics, and dependent Azure resources.
- Treat **SDK/REST/CLI/`azd` automation** as authoritative for prompt agents, Hosted agent versions, traffic routing, tool registration, toolbox configuration, evaluations, and Foundry IQ knowledge objects.
- Treat the **portal as a developer experience**, not the long-term source of truth, for any artifact that changes runtime behavior or governance.
- Allow portal-first authoring in exploration environments, but require promoted artifacts to be recreated or reconciled in source control before they move forward.
- In shared test, UAT, and production-like environments, disallow manual changes except for break-glass incidents and reconcile emergency edits back to Git immediately.
- Run regular drift detection:
  - IaC `what-if` / Terraform plan for management-plane resources
  - API-level comparison for agents, versions, routing, evaluations, tool registrations, and Foundry IQ objects

Relevant references include [Deploy an agent with `azd`](https://learn.microsoft.com/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension), [Agent Service overview](https://learn.microsoft.com/azure/foundry/agents/overview), [Manage hosted agents](https://learn.microsoft.com/azure/foundry/agents/how-to/manage-hosted-agent), [Add a new connection to your project](https://learn.microsoft.com/azure/foundry/how-to/connections-add), [Function calling with Foundry agents](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/function-calling), and [Cloud evaluations](https://learn.microsoft.com/azure/foundry/how-to/develop/cloud-evaluation).