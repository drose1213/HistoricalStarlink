import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { auctionApi } from '@/api/auction'
import type { CardAuction, AuctionDetail, CardBid } from '@/types'
import { getSessionId } from '@/utils/session'

export const useAuctionStore = defineStore('auction', () => {
  const auctions = ref<CardAuction[]>([])
  const total = ref(0)
  const isLoading = ref(false)
  const currentDetail = ref<AuctionDetail | null>(null)

  const activeAuctions = computed(() => auctions.value.filter(a => a.status === 'active'))
  const soldAuctions = computed(() => auctions.value.filter(a => a.status === 'sold'))

  async function load(params: { status?: string; event_id?: string; seller_session_id?: string; page?: number; page_size?: number } = {}) {
    isLoading.value = true
    try {
      const res = await auctionApi.list(params)
      auctions.value = res.data.items || []
      total.value = res.data.total || 0
      return auctions.value
    } finally {
      isLoading.value = false
    }
  }

  async function loadDetail(auctionId: number) {
    isLoading.value = true
    try {
      const res = await auctionApi.detail(auctionId)
      currentDetail.value = res.data
      return res.data
    } finally {
      isLoading.value = false
    }
  }

  async function create(payload: { card_id: number; start_price: number; min_increment?: number; duration_hours?: number; description?: string }) {
    const sid = getSessionId()
    const res = await auctionApi.create({ seller_session_id: sid, ...payload })
    auctions.value.unshift(res.data)
    total.value += 1
    return res.data
  }

  async function placeBid(auctionId: number, amount: number) {
    const sid = getSessionId()
    const res = await auctionApi.bid({ auction_id: auctionId, bidder_session_id: sid, amount })
    // 更新本地缓存中的当前价
    const target = auctions.value.find(a => a.id === auctionId)
    if (target) {
      target.current_price = amount
      target.bid_count = (target.bid_count || 0) + 1
    }
    if (currentDetail.value && currentDetail.value.auction.id === auctionId) {
      currentDetail.value.auction.current_price = amount
      currentDetail.value.auction.bid_count = (currentDetail.value.auction.bid_count || 0) + 1
      // 把之前的领先出价标 false
      currentDetail.value.bids.forEach((b: CardBid) => { b.is_winning = false })
      currentDetail.value.bids.unshift(res.data)
    }
    return res.data
  }

  async function cancel(auctionId: number) {
    const sid = getSessionId()
    await auctionApi.cancel(auctionId, sid)
    const target = auctions.value.find(a => a.id === auctionId)
    if (target) target.status = 'cancelled'
  }

  async function submitReview(auctionId: number, stars: number, comment?: string) {
    const sid = getSessionId()
    const res = await auctionApi.review({ auction_id: auctionId, reviewer_session_id: sid, stars, comment })
    if (currentDetail.value && currentDetail.value.auction.id === auctionId) {
      const existing = currentDetail.value.reviews.find(r => r.reviewer_session_id === sid)
      if (existing) Object.assign(existing, res.data)
      else currentDetail.value.reviews.unshift(res.data)
    }
    return res.data
  }

  return {
    auctions,
    total,
    isLoading,
    currentDetail,
    activeAuctions,
    soldAuctions,
    load,
    loadDetail,
    create,
    placeBid,
    cancel,
    submitReview
  }
})
