import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { parseError } from '../utils/errorHandler.js'
import { NotificationProvider, useNotification } from '../context/NotificationContext.jsx'

function TestNotifierComponent() {
  const { notify, confirm } = useNotification()

  return (
    <div>
      <button onClick={() => notify.success('Record saved successfully.', 'All Good')}>
        Trigger Success
      </button>
      <button onClick={() => notify.error('Validation failed', 'Error Title', { listItems: ['col1', 'col2'] })}>
        Trigger Error With Chips
      </button>
      <button onClick={() => notify.parseError('Missing required columns in student file: emis_id, full_name, grade')}>
        Trigger Missing Column Parse
      </button>
      <button
        onClick={async () => {
          const res = await confirm({ title: 'Delete Item?', message: 'Really delete?', confirmText: 'Yes Delete' })
          if (res) notify.info('User confirmed deletion')
        }}
      >
        Trigger Confirm
      </button>
    </div>
  )
}

describe('Centralized Notification & Error System', () => {
  it('correctly parses missing column validation error into structured notification payload', () => {
    const rawError = 'Missing required columns in student file: emis_id, grade, full_name'
    const parsed = parseError(rawError)

    expect(parsed.title).toBe('Student File Validation Failed')
    expect(parsed.message).toContain('missing 3 required columns')
    expect(parsed.listItems).toEqual(['emis_id', 'grade', 'full_name'])
    expect(parsed.type).toBe('error')
    expect(parsed.suggestion).toBeDefined()
  })

  it('correctly parses HTTP 413 file size exceeded error', () => {
    const err = { status: 413 }
    const parsed = parseError(err)

    expect(parsed.title).toBe('File Size Exceeded')
    expect(parsed.message).toContain('5 MB')
    expect(parsed.type).toBe('error')
  })

  it('correctly parses HTTP 403 access restricted error', () => {
    const err = { status: 403, data: { detail: 'Forbidden for teachers' } }
    const parsed = parseError(err)

    expect(parsed.title).toBe('Access Restricted')
    expect(parsed.message).toBe('Forbidden for teachers')
    expect(parsed.type).toBe('warning')
  })

  it('renders native toast notifications with structured chips and close button', () => {
    render(
      <NotificationProvider>
        <TestNotifierComponent />
      </NotificationProvider>
    )

    // Trigger success toast
    fireEvent.click(screen.getByText('Trigger Success'))
    expect(screen.getByText('All Good')).toBeInTheDocument()
    expect(screen.getByText('Record saved successfully.')).toBeInTheDocument()

    // Trigger structured error toast with column chips
    fireEvent.click(screen.getByText('Trigger Missing Column Parse'))
    expect(screen.getByText('Student File Validation Failed')).toBeInTheDocument()
    expect(screen.getByText('emis_id')).toBeInTheDocument()
    expect(screen.getByText('full_name')).toBeInTheDocument()
    expect(screen.getByText('grade')).toBeInTheDocument()
  })

  it('renders application-native confirmation modal instead of browser confirm()', async () => {
    render(
      <NotificationProvider>
        <TestNotifierComponent />
      </NotificationProvider>
    )

    // Trigger confirm dialog
    fireEvent.click(screen.getByText('Trigger Confirm'))
    expect(screen.getByText('Delete Item?')).toBeInTheDocument()
    expect(screen.getByText('Really delete?')).toBeInTheDocument()

    // Click confirm button
    const confirmBtn = screen.getByRole('button', { name: 'Yes Delete' })
    fireEvent.click(confirmBtn)

    // Verify modal dismissed and confirmation toast triggered
    expect(await screen.findByText('User confirmed deletion')).toBeInTheDocument()
    expect(screen.queryByText('Delete Item?')).not.toBeInTheDocument()
  })
})
