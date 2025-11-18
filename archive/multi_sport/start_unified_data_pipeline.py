#!/usr/bin/env python3
"""
🚀 START UNIFIED DATA PIPELINE
==============================
Käynnistää yhdistetyn datan hakurakenteen ja korkeimman ROI:n analyysin.

Käyttö:
    python start_unified_data_pipeline.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_pipeline_orchestrator import DataPipelineOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🚀 UNIFIED DATA PIPELINE & HIGHEST ROI FRAMEWORK           ║
║  ==========================================================  ║
║                                                              ║
║  Automaattinen datan hakeminen ja ROI-analyysi              ║
║  - Hakee pelit useista lähteistä                            ║
║  - Kerää tilastot kaikille lajeille                         ║
║  - Laskee korkeimman ROI:n                                   ║
║  - Synkronoi Notioniin                                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Initialize orchestrator
        logger.info("🔧 Initializing pipeline...")
        orchestrator = DataPipelineOrchestrator()
        
        # Show initial statistics
        print("\n📊 Initial Statistics:")
        stats = orchestrator.get_statistics()
        for key, value in stats.items():
            if key != 'running':
                print(f"   {key}: {value}")
        
        # Start pipeline
        print("\n🚀 Starting pipeline...")
        print("   Press Ctrl+C to stop\n")
        
        await orchestrator.start()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Stopping pipeline...")
        await orchestrator.stop()
        print("\n✅ Pipeline stopped")
        
        # Show final statistics
        print("\n📊 Final Statistics:")
        final_stats = orchestrator.get_statistics()
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

