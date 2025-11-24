# Example: Corporate Website Discovery

#Demonstrates how to use the DSI Website Discovery module to find
#corporate websites for companies.


import sys
from pathlib import Path

# Add models to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from website_discovery.dsi_website_discovery import CorporateWebsiteDiscovery  # noqa: E402


def example_single_company():
    '''Example: Discover website for a single company'''
    print('=' * 80)
    print('EXAMPLE 1: Single Company Discovery')
    print('=' * 80)

    # Initialize discovery
    discovery = CorporateWebsiteDiscovery(timeout=10)

    # Discover Marks & Spencer
    print('\n🔍 Discovering website for: Marks and Spencer')
    result = discovery.discover('Marks and Spencer', use_search=False)

    # Display results
    print(f'\n✅ Discovery completed in {result.discovery_time:.2f}s')
    print(f'Success: {result.success}')
    print(f'Total candidates found: {result.total_candidates}')
    print(f'Strategies used: {', '.join(result.strategies_used)}')

    if result.best_match:
        print(f'\n🏆 BEST MATCH:')
        print(f'  URL: {result.best_match.url}')
        print(f'  Confidence Score: {result.best_match.confidence_score:.1f}/100')
        print(f'  Discovery Method: {result.best_match.discovery_method.value}')
        print(f'  Title: {result.best_match.title}')
        print(f'  Corporate Indicators Found: {len(result.best_match.corporate_indicators)}')

        if result.best_match.corporate_indicators:
            print(f'  Key Indicators:')
            for indicator in result.best_match.corporate_indicators[:5]:
                print(f'    • {indicator}')

    # Show all candidates
    if result.all_candidates:
        print(f'\n📋 ALL CANDIDATES:')
        for idx, candidate in enumerate(result.all_candidates[:10]):
            print(f'  {idx+1}. {candidate.url}')
            print(f'     Score: {candidate.confidence_score:.1f}/100')
            print(f'     Method: {candidate.discovery_method.value}')
            print()


def example_batch_discovery():
    '''Example: Discover websites for multiple companies'''
    print('\n' + '=' * 80)
    print('EXAMPLE 2: Batch Company Discovery')
    print('=' * 80)

    companies = [
        'Marks and Spencer',
        'MS Amlin',
        'Brit',
    ]

    discovery = CorporateWebsiteDiscovery(timeout=10)

    print(f'\n🔍 Discovering websites for {len(companies)} companies...')
    print(f'Companies: {', '.join(companies)}')

    results = discovery.discover_batch(companies, use_search=False, delay=1.0)

    # Display results table
    print(f'\n{'='*80}')
    print(f'{'Company':<25} {'Success':<10} {'Best Match':<45}')
    print(f'{'='*80}')

    for company_name, result in results.items():
        success = '✓' if result.success else '✗'
        best_url = result.best_match.url if result.best_match else 'Not found'
        if len(best_url) > 43:
            best_url = best_url[:40] + '...'

        print(f'{company_name:<25} {success:<10} {best_url:<45}')

    # Detailed results
    print(f'\n{'='*80}')
    print('DETAILED RESULTS')
    print(f'{'='*80}')

    for company_name, result in results.items():
        print(f'\n{company_name}:')
        print(f'  Candidates: {result.total_candidates}')
        print(f'  Discovery Time: {result.discovery_time:.2f}s')

        if result.best_match:
            print(f'  Best Match: {result.best_match.url}')
            print(f'  Confidence: {result.best_match.confidence_score:.1f}/100')
            print(f'  Indicators: {len(result.best_match.corporate_indicators)}')


def example_with_domain_hint():
    '''Example: Using domain hints for better accuracy'''
    print('\n' + '=' * 80)
    print('EXAMPLE 3: Discovery with Domain Hint')
    print('=' * 80)

    discovery = CorporateWebsiteDiscovery()

    # Without hint
    print('\n🔍 Discovering Marks & Spencer WITHOUT hint...')
    result_no_hint = discovery.discover('Marks and Spencer', use_search=False)

    if result_no_hint.best_match:
        print(f'  Found: {result_no_hint.best_match.url}')
        print(f'  Score: {result_no_hint.best_match.confidence_score:.1f}/100')

    # With hint
    print('\n🔍 Discovering Marks & Spencer WITH hint...')
    result_with_hint = discovery.discover(
        'Marks and Spencer',
        domain_hint='corporate.marksandspencer.com',
        use_search=False,
    )

    if result_with_hint.best_match:
        print(f'  Found: {result_with_hint.best_match.url}')
        print(f'  Score: {result_with_hint.best_match.confidence_score:.1f}/100')
        print(f'  Method: {result_with_hint.best_match.discovery_method.value}')

    # Compare
    print('\n📊 COMPARISON:')
    print(f'  Without hint: {result_no_hint.total_candidates} candidates')
    print(f'  With hint: {result_with_hint.total_candidates} candidates')
    print(f'  Hint prioritized: {result_with_hint.best_match.discovery_method.value == 'manual'}')


def example_detailed_analysis():
    '''Example: Detailed analysis of discovery results'''
    print('\n' + '=' * 80)
    print('EXAMPLE 4: Detailed Discovery Analysis')
    print('=' * 80)

    discovery = CorporateWebsiteDiscovery()

    print('\n🔍 Analyzing Marks & Spencer website discovery...')
    result = discovery.discover('Marks and Spencer', use_search=False)

    if not result.best_match:
        print('❌ No match found')
        return

    candidate = result.best_match

    print(f'\n🏆 BEST MATCH ANALYSIS:')
    print(f'  URL: {candidate.url}')
    print(f'  Overall Score: {candidate.confidence_score:.1f}/100')

    if candidate.validation_result:
        val = candidate.validation_result
        print(f'\n📊 VALIDATION DETAILS:')
        print(f'  Status Code: {val.status_code}')
        print(f"  SSL Valid: {'✓' if val.ssl_valid else '✗'}")
        print(f'  Response Time: {val.response_time:.2f}s')

        print(f'\n✓ INDICATORS:')
        for key, value in val.indicators.items():
            status = '✓' if value else '✗'
            print(f'    {status} {key.replace('_', ' ').title()}')

        if val.corporate_indicators:
            print(f'\n🏢 CORPORATE CONTENT FOUND:')
            for indicator in val.corporate_indicators:
                print(f'    • {indicator.title()}')

        if val.title:
            print(f'\n📄 PAGE METADATA:')
            print(f'  Title: {val.title[:80]}')
            if val.description:
                print(f'  Description: {val.description[:100]}...')


def example_api_integration():
    '''Example: Using search API integration (requires API keys)'''
    print('\n' + '=' * 80)
    print('EXAMPLE 5: Search API Integration')
    print('=' * 80)

    # Initialize with API keys (from environment variables)
    discovery = CorporateWebsiteDiscovery(
        # google_api_key='your_key_here',  # Set via environment
        # google_cx='your_cx_here',
        timeout=10
    )

    print('\n🔍 Discovering with search engine support...')
    print('ℹ️  Note: Requires Google Custom Search API key')

    result = discovery.discover('Marks and Spencer', use_search=True)

    if result.success:
        print(f'\n✅ Found via: {', '.join(result.strategies_used)}')
        print(f'Best match: {result.best_match.url}')
        print(f'Total candidates: {result.total_candidates}')
    else:
        print('\n⚠️  Search API not configured, using domain generation only')
        print('Set GOOGLE_API_KEY and GOOGLE_CX environment variables to enable')


def example_cache_usage():
    '''Example: Using cache for repeated lookups'''
    print('\n' + '=' * 80)
    print('EXAMPLE 6: Cache Usage')
    print('=' * 80)

    discovery = CorporateWebsiteDiscovery(use_cache=True)

    # First lookup
    print('\n🔍 First lookup (will be cached)...')
    import time

    start = time.time()
    result1 = discovery.discover('Marks and Spencer', use_search=False)
    time1 = time.time() - start

    print(f'  Time: {time1:.2f}s')
    print(f'  Candidates: {result1.total_candidates}')

    # Second lookup (from cache)
    print('\n🔍 Second lookup (from cache)...')
    start = time.time()
    result2 = discovery.discover('Marks and Spencer', use_search=False)
    time2 = time.time() - start

    print(f'  Time: {time2:.2f}s')
    print(f'  Candidates: {result2.total_candidates}')

    # Compare
    print(f'\n📊 CACHE PERFORMANCE:')
    print(f'  First lookup: {time1:.3f}s')
    print(f'  Cached lookup: {time2:.3f}s')
    print(f'  Speedup: {(time1/time2):.1f}x faster')

    # Cache stats
    stats = discovery.get_cache_stats()
    print(f'\n💾 Cache Stats:')
    print(f'  Cached results: {stats['cached_results']}')


if __name__ == '__main__':
    print('\n' + '=' * 80)
    print('DSI CORPORATE WEBSITE DISCOVERY EXAMPLES')
    print('=' * 80)

    example_single_company()
    example_batch_discovery()
    example_with_domain_hint()
    example_detailed_analysis()
    example_api_integration()
    example_cache_usage()

    print('\n' + '=' * 80)
    print('✅ All examples completed!')
    print('=' * 80 + '\n')
