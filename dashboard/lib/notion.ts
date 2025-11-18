import { Client } from '@notionhq/client';
import { NotionSyncStatus } from '@/types';

let notionClient: Client | null = null;

export function initializeNotionClient(token?: string): Client | null {
  const notionToken = token || process.env.NOTION_TOKEN;
  
  if (!notionToken) {
    return null;
  }

  if (!notionClient) {
    notionClient = new Client({
      auth: notionToken,
    });
  }

  return notionClient;
}

export async function getNotionStatus(): Promise<NotionSyncStatus> {
  const client = initializeNotionClient();
  
  if (!client) {
    return {
      connected: false,
      error: 'Notion token not configured',
      databases: {},
    };
  }

  try {
    // Try to search for databases to verify connection
    const response = await client.search({
      filter: {
        property: 'object',
        value: 'database',
      },
    });

    // Extract database IDs from config if available
    const databases: NotionSyncStatus['databases'] = {};
    
    // Try to find databases by title
    for (const result of response.results) {
      if ('title' in result && result.title) {
        const title = result.title[0]?.plain_text?.toLowerCase() || '';
        if (title.includes('tennis')) {
          databases.tennis = result.id;
        } else if (title.includes('football') || title.includes('soccer')) {
          databases.football = result.id;
        } else if (title.includes('basketball')) {
          databases.basketball = result.id;
        } else if (title.includes('hockey') || title.includes('ice')) {
          databases.ice_hockey = result.id;
        } else if (title.includes('roi') || title.includes('analysis')) {
          databases.roi_analysis = result.id;
        }
      }
    }

    return {
      connected: true,
      databases,
      lastSync: new Date().toISOString(),
    };
  } catch (error: any) {
    return {
      connected: false,
      error: error.message || 'Failed to connect to Notion',
      databases: {},
    };
  }
}

export async function syncOpportunityToNotion(
  opportunity: any,
  databaseId: string
): Promise<boolean> {
  const client = initializeNotionClient();
  
  if (!client || !databaseId) {
    return false;
  }

  try {
    await client.pages.create({
      parent: {
        database_id: databaseId,
      },
      properties: {
        Match: {
          title: [
            {
              text: {
                content: opportunity.match || 'Unknown Match',
              },
            },
          ],
        },
        Sport: {
          select: {
            name: opportunity.sport || 'Unknown',
          },
        },
        ROI: {
          number: opportunity.roi || 0,
        },
        Edge: {
          number: opportunity.edge || 0,
        },
        Confidence: {
          number: opportunity.confidence ? opportunity.confidence * 100 : 0,
        },
        Odds: {
          number: opportunity.odds || 0,
        },
        Status: {
          select: {
            name: opportunity.status || 'upcoming',
          },
        },
      },
    });

    return true;
  } catch (error) {
    console.error('Error syncing to Notion:', error);
    return false;
  }
}

export async function syncMultipleOpportunities(
  opportunities: any[],
  databaseId: string
): Promise<{ success: number; failed: number }> {
  let success = 0;
  let failed = 0;

  for (const opportunity of opportunities) {
    const result = await syncOpportunityToNotion(opportunity, databaseId);
    if (result) {
      success++;
    } else {
      failed++;
    }
    
    // Rate limiting - wait 300ms between requests
    await new Promise((resolve) => setTimeout(resolve, 300));
  }

  return { success, failed };
}

