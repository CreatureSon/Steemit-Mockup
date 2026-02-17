const fs = require('fs');
const dsteem = require('dsteem');
const { franc } = require('franc');
const { AkismetClient } = require('akismet-api');
const filter = require('leo-profanity');

const client = new dsteem.Client('https://api.steemit.com');
const filePath = './posts.json';

// Akismet Setup
const AKISMET_KEY = process.env.AKISMET_KEY || '';
const AKISMET_BLOG = "https://steemit.com/";

const akismet = new AkismetClient({ key: AKISMET_KEY, blog: AKISMET_BLOG });

const STEEMIT_SPAM_INDICATORS = [
  '@steemcleaners',
  '@spaminator'
];

// Verify Akismet key on startup
async function verifyAkismet() {
  if (!AKISMET_KEY) {
    console.warn('WARNING: AKISMET_KEY not set. Akismet checks will be skipped.');
    return false;
  }
  try {
    const isValid = await akismet.verifyKey();
    if (!isValid) {
      console.warn('WARNING: Akismet key is invalid. Akismet checks will be skipped.');
    }
    return isValid;
  } catch (e) {
    console.warn('WARNING: Could not reach Akismet:', e.message);
    return false;
  }
}

/**
 * Check if text contains profanity
 */
function containsProfanity(text) {
  if (!text) return false;
  return filter.check(text);
}

/**
 * Check if text looks like spam
 */
async function isSpam(text, author, reputation, akismetReady) {
  if (!text) return false;
  
  const lowerText = text.toLowerCase();
  
  // Check for Steemit-specific spam indicators
  if (STEEMIT_SPAM_INDICATORS.some(indicator => 
    lowerText.includes(indicator.toLowerCase())
  )) return true;
    
  // Check for very low reputation (likely spam account)
  const hasLowReputation = reputation < 10;
  
  // Check for excessive repetition (spam often repeats phrases)
  const words = text.split(/\s+/);
  const uniqueWords = new Set(words.map(w => w.toLowerCase()));
  const repetitionRatio = uniqueWords.size / words.length;
  const isRepetitive = words.length > 50 && repetitionRatio < 0.3;

  if (hasLowReputation && isRepetitive) return true;
  
  if (!akismetReady) return false;

  try {
    return await akismet.checkSpam({
      user_ip: '127.0.0.1',
      user_agent: 'SteemitIngest/1.0',
      content: text,
      name: author,
      type: 'comment'
    });
  } catch (e) {
    console.error('Error checking spam with Akismet:', e.message);
    return false;
  }
}

async function fetchPostJson(author, permlink, category) {
  const url = `https://steemit.com/${category}/@${author}/${permlink}.json`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      console.error(`Failed to fetch ${url}: ${response.status}`);
      return null;
    }

    const data = await response.json();
    return data.post;
  } catch (error) {
    console.error(`Error fetching ${url}:`, error);
    return null;
  }
}

async function fetchAuthorProfile(author) {
  let authorProfileImage = '';
  let authorReputation = 0;

  try {
    const accounts = await client.database.getAccounts([author]);
    if (accounts && accounts.length > 0) {
      const account = accounts[0];

      let metadata = null;

      if (account.posting_json_metadata) {
        try {
          metadata = typeof account.posting_json_metadata === 'string'
            ? JSON.parse(account.posting_json_metadata)
            : account.posting_json_metadata;

          authorProfileImage = metadata?.profile?.profile_image || '';
        } catch (e) {
          console.error(`Error parsing posting_json_metadata for author ${author}:`);
        }
      }

      if (!authorProfileImage && account.json_metadata) {
        try {
          const metadata = typeof account.json_metadata === 'string'
            ? JSON.parse(account.json_metadata)
            : account.json_metadata;

          authorProfileImage = metadata?.profile?.profile_image || '';
        } catch (e) {
          console.error(`Error parsing json_metadata for author ${author}:`);
        }
      }

      if (account.reputation) {
        const rep = account.reputation;
        const isNegative = rep < 0;
        let reputationLevel = Math.log10(Math.abs(rep)) - 9;
        reputationLevel = Math.max(reputationLevel * 9 + 25, 0);
        authorReputation = Math.floor(reputationLevel);
        if (isNegative) authorReputation *= -1;
      }
    }
  } catch (e) {
    console.error(`Error fetching profile for author ${author}:`, e.message || String(e));
  }

  return { authorProfileImage, authorReputation };
}

async function fetchComments(author, permlink, akismetReady) {
  // Only fetch if there are children
  const replies = await client.database.call('get_content_replies', [author, permlink]);

  // Map each reply to only the fields we care about
  const mapped = await Promise.all(replies.map(async reply => {

    let replyData = await fetchPostJson(reply.author, reply.permlink, reply.category);

    if (!replyData) {
      replyData = reply;
    }

    // Fetch author profile for each comment
    const { authorProfileImage, authorReputation } = await fetchAuthorProfile(replyData.author);

    // Filter out comments with profanity or spam
    if (containsProfanity(replyData.author) || 
        containsProfanity(replyData.body) ||
        await isSpam(replyData.body, replyData.author, authorReputation, akismetReady)) {
      console.log(`  Filtered comment by ${replyData.author} (profanity/spam)`);
      return null;
    }

    const nestedReplies = reply.children > 0
      ? await fetchComments(reply.author, reply.permlink, akismetReady)
      : [];

    return {
      author: replyData.author,
      author_image: authorProfileImage,
      author_reputation: authorReputation,
      permlink: replyData.permlink,
      body: replyData.body,
      created: new Date(replyData.created).toISOString(),
      votes: replyData.net_votes || reply.net_votes,
      repliesCount: replyData.children || reply.children,
      replies: nestedReplies
    };
  }));

  return mapped.filter(r => r !== null); // remove any nulls
}

(async function main() {

  // Verify Akismet key is ready
  const akismetReady = await verifyAkismet();
  if (akismetReady) {
    console.log('Akismet spam detection: ACTIVE');
  } else {
    console.log('Akismet spam detection: INACTIVE');
  }

  const tags = ['food', 'travel', 'sports', 'home', 'life', 'work'];
  let allEnglishPosts = [];

  for (const tag of tags) {
    console.log(`\nFetching posts for tag: ${tag}...`);
    
    const result = await client.database.getDiscussions('trending', {
      tag: tag,
      limit: 75
    });

    const englishPosts = (await Promise.all(result.map(async post => {
    
      // Only English posts
      if (post.body && franc(post.body, { minLength: 10 }) === 'eng') {

        const fullPostData = await fetchPostJson(post.author, post.permlink, post.category);

        if (!fullPostData) {
          return null;
        }

        let json = {};
        try { 
          json = typeof fullPostData.json_metadata === 'string'
            ? JSON.parse(fullPostData.json_metadata)
            : (fullPostData.json_metadata || {});
        } catch (e) {
          console.error(`Error parsing json_metadata for ${fullPostData.author}/${fullPostData.permlink}:`, e);
          json = {};
        }

        let imageUrl = json?.image?.[0] || '';

        if (!imageUrl) {
          const imageMatch = fullPostData.body.match(/!\[([^\]]*)\]\(([^\)]+)\)/);
          imageUrl = imageMatch ? imageMatch[2] : '';
        }

        const category = fullPostData.category;
        let categoryName = `#${category}`;

        if (category && /^hive-\d+$/.test(category)) {
          try {
            const response = await fetch('https://api.steemit.com', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'bridge.get_community',
                params: { name: category },
                id: 1
              })
            });
            const data = await response.json();
            if (data.result && data.result.title) {
                  categoryName = data.result.title;
            }
          } catch (e) {
            console.error(`Error fetching community info for ${category}:`, e.message || String(e));
          }
        }

        const { authorProfileImage, authorReputation } = await fetchAuthorProfile(fullPostData.author);

        // Filter out posts with profanity or spam
        if (containsProfanity(fullPostData.author) || 
            containsProfanity(fullPostData.title) ||
            containsProfanity(fullPostData.body) ||
            await isSpam(fullPostData.body, fullPostData.author, authorReputation, akismetReady)) {
          console.log(`Filtered post by ${fullPostData.author}: "${fullPostData.title}" (profanity/spam)`);
          return null;
        }

        const postData = {
            author: fullPostData.author,
            author_image: authorProfileImage,
            author_reputation: authorReputation,
            title: fullPostData.title,
            body: fullPostData.body,
            category: category,
            category_name: categoryName,
            image: imageUrl,
            permlink: fullPostData.permlink,
            created: fullPostData.created,
            children: fullPostData.children,
            votes: fullPostData.net_votes,
            payout: fullPostData.pending_payout_value
        };

        postData.comments = fullPostData.children > 0 ?
            await fetchComments(fullPostData.author, fullPostData.permlink, akismetReady) : [];
        return postData;
      }

      return null;
      }))).filter(p => p !== null); // remove nulls
    
    console.log(`Found ${englishPosts.length} English posts for tag: ${tag}`);
    allEnglishPosts = allEnglishPosts.concat(englishPosts);
  }
    
  // Prepare export JSON for Django or other use
  const exportPosts = allEnglishPosts.map(p => ({
    author: p.author,
    author_image: p.author_image,
    author_reputation: p.author_reputation,
    permlink: p.permlink,
    category: p.category,
    category_name: p.category_name,
    title: p.title,
    text: p.body,
    image: p.image,
    votes: p.votes,
    payout: p.payout,
    created: new Date(p.created).toISOString(),
    comments: p.comments
  }));

  fs.writeFileSync(filePath, JSON.stringify(exportPosts, null, 2));
  console.log(`Saved ${exportPosts.length} English posts`);
})();