'use client'

import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react'
import {
  Activity,
  ArrowUp,
  Copy,
  MessageCircle,
  Plus,
  Share2,
  Trash2,
  X,
} from 'lucide-react'
import { useAnalysis } from '@/components/analysis-context'
import { BarChart } from '@/components/finance-shell'
import { formatConversationForSharing, type ChatConversation } from '@/lib/chat-history'

const suggestions = [
  'Can I afford a ₹5L personal loan over 3 years?',
  'I want to buy a car for ₹10L at 8% interest for 5 years.',
  'Should I take an education loan of ₹20L for 4 years?',
  'I am planning to buy a house with a ₹50L mortgage for 20 years.',
]

function conversationText(conversation: ChatConversation) {
  return formatConversationForSharing(conversation)
}

async function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      // Try the legacy copy command for browsers that reject Clipboard API access.
    }
  }

  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.setAttribute('readonly', '')
  textArea.style.position = 'fixed'
  textArea.style.opacity = '0'
  document.body.appendChild(textArea)
  textArea.select()
  const copied = document.execCommand('copy')
  document.body.removeChild(textArea)
  return copied
}

function ShareConversationDialog({
  conversation,
  onClose,
}: {
  conversation: ChatConversation
  onClose: () => void
}) {
  const [feedback, setFeedback] = useState('')
  const [busy, setBusy] = useState(false)
  const [canShare, setCanShare] = useState(false)
  const copyButton = useRef<HTMLButtonElement>(null)
  const text = conversationText(conversation)

  useEffect(() => {
    setCanShare(typeof navigator.share === 'function')
    copyButton.current?.focus()
    function handleEscape(event: globalThis.KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  async function handleCopy() {
    setBusy(true)
    try {
      if (await copyText(text)) setFeedback('Conversation text copied to your clipboard.')
      else setFeedback('Copy was not available. Select and copy the conversation text below.')
    } catch {
      setFeedback('We could not copy the conversation. Select and copy the text below.')
    } finally {
      setBusy(false)
    }
  }

  async function handleShare() {
    if (!navigator.share) return
    setBusy(true)
    try {
      await navigator.share({ title: `FutureFund: ${conversation.title}`, text })
      setFeedback('Conversation shared.')
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        setFeedback('Sharing cancelled.')
      } else {
        setFeedback('Device sharing failed. You can copy the conversation text instead.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#172a2a]/40 p-4 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="share-dialog-title"
        onKeyDown={(event: KeyboardEvent<HTMLElement>) => {
          if (event.key !== 'Tab') return
          const focusable = event.currentTarget.querySelectorAll<HTMLElement>(
            'button:not([disabled]), textarea:not([disabled])',
          )
          if (!focusable.length) return
          const first = focusable[0]
          const last = focusable[focusable.length - 1]
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault()
            last.focus()
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault()
            first.focus()
          }
        }}
        className="w-full max-w-lg rounded-[24px] border border-[#e4dbcf] bg-[#fffdf9] p-6 shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#a17a35]">Conversation</p>
            <h2 id="share-dialog-title" className="mt-2 text-xl font-semibold text-[#263d39]">Share conversation</h2>
            <p className="mt-2 text-sm text-[#78827d]">
              Share or copy this transcript as text. This does not create a public link.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close share dialog"
            className="rounded-lg p-2 text-[#68756e] hover:bg-[#f7f3ec] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#a17a35]"
          >
            <X size={18} />
          </button>
        </div>
        <label htmlFor="share-transcript" className="sr-only">Conversation text to share</label>
        <textarea
          id="share-transcript"
          readOnly
          value={text}
          rows={7}
          className="mt-5 w-full resize-y rounded-xl border border-[#e4dbcf] bg-white p-3 text-sm leading-6 text-[#40524b]"
        />
        {feedback && (
          <p role="status" className="mt-3 text-sm text-[#35624f]">{feedback}</p>
        )}
        <div className="mt-5 flex flex-wrap justify-end gap-3">
          {canShare && (
            <button
              type="button"
              onClick={() => void handleShare()}
              disabled={busy}
              className="inline-flex items-center gap-2 rounded-xl border border-[#ded8ce] px-4 py-2.5 text-sm font-semibold text-[#46544e] hover:bg-[#f8f3eb] disabled:opacity-50"
            >
              <Share2 size={16} /> Share with device
            </button>
          )}
          <button
            ref={copyButton}
            type="button"
            onClick={() => void handleCopy()}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-xl bg-[#17352f] px-4 py-2.5 text-sm font-semibold text-[#f5d282] hover:bg-[#285248] disabled:opacity-50"
          >
            <Copy size={16} /> Copy conversation
          </button>
        </div>
      </section>
    </div>
  )
}

export function DecisionChat() {
  const {
    messages,
    analysis,
    loading,
    error,
    submit,
    history,
    historyLoaded,
    historyError,
    currentConversationId,
    selectConversation,
    startNewConversation,
    deleteConversation,
  } = useAnalysis()
  const [question, setQuestion] = useState('')
  const [shareConversation, setShareConversation] = useState<ChatConversation | null>(null)
  const shareTrigger = useRef<HTMLButtonElement | null>(null)
  const closeShareDialog = useCallback(() => {
    setShareConversation(null)
    shareTrigger.current?.focus()
  }, [])

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing && event.keyCode !== 229) {
      event.preventDefault()
      void submit(question)
      setQuestion('')
    }
  }

  function handleDelete(conversation: ChatConversation) {
    const confirmed = window.confirm(`Delete “${conversation.title}”? This conversation will be permanently removed from this browser.`)
    if (confirmed) deleteConversation(conversation.id)
  }

  return (
    <div className="chatbot-interface mx-auto grid w-full max-w-[1440px] gap-7 px-5 pb-20 pt-8 lg:grid-cols-[270px_minmax(0,1fr)] lg:gap-x-12 lg:px-8 xl:grid-cols-[270px_minmax(0,1fr)]">
      <aside
        aria-label="Chat history"
        className="h-fit rounded-[22px] border border-[#e4dbcf] bg-white/75 p-4 shadow-[0_10px_32px_rgba(79,61,34,0.045)] lg:sticky lg:top-24"
      >
        <div className="flex items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-[#34443e]">Chat history</h2>
            <p className="mt-1 text-xs text-[#78827d]">Saved in this browser</p>
          </div>
          <button
            type="button"
            onClick={startNewConversation}
            disabled={loading}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-xl bg-[#17352f] px-3 py-2 text-xs font-semibold text-[#f5d282] transition hover:bg-[#285248] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Plus size={15} /> New chat
          </button>
        </div>

        {historyError && <p role="alert" className="mt-3 text-xs leading-5 text-[#a34b3b]">{historyError}</p>}
        {!historyLoaded ? (
          <p className="mt-4 text-sm text-[#78827d]">Loading conversations…</p>
        ) : history.length === 0 ? (
          <p className="mt-4 rounded-xl bg-[#f8f3eb] p-3 text-sm leading-5 text-[#78827d]">
            No saved conversations yet. Your completed chats will appear here.
          </p>
        ) : (
          <ul className="mt-3 max-h-[min(46vh,28rem)] space-y-2 overflow-y-auto pr-1 lg:max-h-[calc(100vh-12rem)]">
            {history.map((conversation) => {
              const active = conversation.id === currentConversationId
              return (
                <li
                  key={conversation.id}
                  className={`rounded-xl border p-2.5 transition ${active ? 'border-[#c8a256] bg-[#fffaf0]' : 'border-transparent bg-[#faf7f1] hover:border-[#e4dbcf]'}`}
                >
                  <button
                    type="button"
                    onClick={() => selectConversation(conversation.id)}
                    disabled={loading}
                    aria-current={active ? 'true' : undefined}
                    className="block w-full rounded-lg text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#a17a35] disabled:cursor-not-allowed"
                  >
                    <span className="block break-words text-[14px] font-semibold leading-5 text-[#34443e] sm:text-[15px] sm:leading-[1.4]">
                      {conversation.title}
                    </span>
                    <span className="mt-1 block text-xs leading-4 text-[#78827d]">
                      {new Date(conversation.updatedAt).toLocaleDateString()} · {conversation.messages.length} messages
                    </span>
                  </button>
                  <div className="mt-2 flex justify-end gap-1">
                    <button
                      type="button"
                      onClick={(event) => {
                        shareTrigger.current = event.currentTarget
                        setShareConversation(conversation)
                      }}
                      aria-label={`Share conversation: ${conversation.title}`}
                      title="Share conversation"
                      className="rounded-lg p-2 text-[#53665c] transition hover:bg-[#e8f0e7] hover:text-[#245542] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#a17a35]"
                    >
                      <Share2 size={16} />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(conversation)}
                      disabled={loading}
                      aria-label={`Delete conversation: ${conversation.title}`}
                      title="Delete conversation"
                      className="rounded-lg p-2 text-[#8e4e3b] transition hover:bg-[#f8eee4] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#a17a35] disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </aside>

      <div className="min-w-0 xl:col-start-2 xl:row-start-1 xl:w-full xl:max-w-[760px] xl:justify-self-center">
        <section className="mx-auto mt-3 max-w-[760px] text-center sm:mt-8">
          <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#e2eee4] text-[#306151]"><MessageCircle size={21} /></div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-[#a17a35]">Your financial co-pilot</p>
          <h1 className="text-4xl font-semibold tracking-[-0.055em] text-[#172a2a] sm:text-[50px] sm:leading-[1.06]">What financial decision is on your mind?</h1>
          <p className="mx-auto mt-5 max-w-[510px] text-[15px] leading-7 text-[#6c7771]">Ask a question. Explore the possibilities. Understand the impact before you decide.</p>
          <div className="mt-10 rounded-[24px] border border-[#dcd5c9] bg-white p-3 text-left shadow-[0_12px_36px_rgba(79,61,34,0.07)] focus-within:border-[#bd9b58] focus-within:ring-4 focus-within:ring-[#e9d9b4]/50">
            {messages.length > 0 && (
              <div className="mb-3 max-h-[60vh] space-y-2 overflow-y-auto px-2 pt-1" aria-live="polite">
                {messages.map((message, index) => (
                  <div key={`${message.role}-${index}`} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] whitespace-pre-wrap break-words rounded-2xl px-4 py-3 text-[16px] leading-7 ${message.role === 'user' ? 'bg-[#17352f] text-white' : 'bg-[#f7f3ec] text-[#46544e]'}`}>
                      {message.text}
                      {message.graph && (
                        <div className="mt-5 rounded-xl bg-white p-4 shadow-sm">
                          <p className="mb-4 text-sm font-semibold text-[#34443e]">Monthly Projection</p>
                          <BarChart values={[message.graph.savings, message.graph.expenses]} labels={['Savings', 'Expenses']} />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              rows={3}
              placeholder="e.g. Can I afford a ₹5 lakh personal loan over 3 years?"
              className="w-full resize-none bg-transparent px-2 py-1 text-[17px] leading-7 outline-none placeholder:text-[#8d9891]"
              aria-label="Financial question"
            />
            <div className="flex items-center justify-between px-1 pt-2">
              <span className="text-[14px] leading-5 text-[#7d8982]">Shift + Enter for a new line</span>
              <button
                onClick={() => { void submit(question); setQuestion('') }}
                disabled={!question.trim() || loading || !historyLoaded}
                aria-label="Send question"
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#17352f] text-[#f5d282] transition hover:bg-[#285248] disabled:cursor-not-allowed disabled:opacity-35"
              >
                {loading ? <Activity size={17} className="animate-pulse" /> : <ArrowUp size={18} />}
              </button>
            </div>
          </div>
          {error && <p role="alert" className="mt-3 text-sm text-[#a34b3b]">{error}</p>}
          <div className="mt-5 flex flex-wrap justify-center gap-2">
            {suggestions.map((suggestion) => (
              <button key={suggestion} onClick={() => setQuestion(suggestion)} className="rounded-full border border-[#ded8ce] bg-white/55 px-3.5 py-2 text-xs text-[#64716b] transition hover:border-[#c5a866] hover:bg-white hover:text-[#34534a]">{suggestion}</button>
            ))}
          </div>
        </section>

      </div>
      {shareConversation && (
        <ShareConversationDialog
          key={shareConversation.id}
          conversation={shareConversation}
          onClose={closeShareDialog}
        />
      )}
    </div>
  )
}
