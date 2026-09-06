import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { artworkUrl, uploadArtwork, type UploadedArtwork } from '../api/cms'
import { getApiErrorMessage } from '../api/client'

type ArtworkSlot = 'poster' | 'banner' | 'thumbnail'
interface FileState { file: File; previewUrl: string }
const rules: Record<ArtworkSlot, { label: string; dimensions: string }> = {
  poster: { label: 'Poster', dimensions: '600 × 900 px' },
  banner: { label: 'Banner', dimensions: '1280 × 720 px' },
  thumbnail: { label: 'Thumbnail', dimensions: '640 × 360 px' },
}

export function ArtworkUploadPanel({ showId }: { showId: number }) {
  const [files, setFiles] = useState<Partial<Record<ArtworkSlot, FileState>>>({})
  const [uploaded, setUploaded] = useState<Partial<Record<ArtworkSlot, UploadedArtwork>>>({})
  const [fileError, setFileError] = useState<string | null>(null)
  const [progress, setProgress] = useState<Partial<Record<ArtworkSlot, number>>>({})
  const uploadMutation = useMutation({
    mutationFn: ({ slot, file }: { slot: ArtworkSlot; file: File }) => uploadArtwork(showId, slot, file, (percent) => setProgress((current) => ({ ...current, [slot]: percent }))),
    onSuccess: (artwork, { slot }) => { setUploaded((current) => ({ ...current, [slot]: artwork })); setProgress((current) => ({ ...current, [slot]: 100 })) },
  })

  function selectFile(slot: ArtworkSlot, file: File | undefined) {
    setFileError(null)
    if (!file) return
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) return setFileError('Choose a JPEG, PNG, or WebP image.')
    if (file.size > 200 * 1024) return setFileError('Artwork file size must not exceed 200 KB.')
    const oldPreview = files[slot]?.previewUrl
    if (oldPreview) URL.revokeObjectURL(oldPreview)
    setFiles((current) => ({ ...current, [slot]: { file, previewUrl: URL.createObjectURL(file) } }))
    setProgress((current) => ({ ...current, [slot]: 0 }))
  }

  return <section className="artwork-panel"><div><p className="eyebrow">Artwork</p><h2>Artwork upload</h2><p className="muted">JPEG, PNG, or WebP only. Maximum file size: 200 KB. The backend verifies exact dimensions and image validity.</p></div>
    {fileError || uploadMutation.isError ? <p className="form-error" role="alert">{fileError ?? getApiErrorMessage(uploadMutation.error)}</p> : null}
    <div className="artwork-grid">{(Object.keys(rules) as ArtworkSlot[]).map((slot) => { const currentFile = files[slot]; const savedArtwork = uploaded[slot]; const imageSource = currentFile?.previewUrl ?? artworkUrl(savedArtwork?.image_url ?? null); const isUploading = uploadMutation.isPending && uploadMutation.variables?.slot === slot; return <article className="artwork-slot" key={slot}><div className="artwork-preview">{imageSource ? <img src={imageSource} alt={`${rules[slot].label} preview`} /> : <span>No image selected</span>}</div><h3>{rules[slot].label}</h3><p className="field-note">Required: {rules[slot].dimensions}</p><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => selectFile(slot, event.target.files?.[0])} />{currentFile ? <p className="field-note">{currentFile.file.name}</p> : null}{savedArtwork ? <p className="upload-success">Uploaded: {savedArtwork.width} × {savedArtwork.height}px</p> : null}<button type="button" disabled={!currentFile || uploadMutation.isPending} onClick={() => currentFile && uploadMutation.mutate({ slot, file: currentFile.file })}>{isUploading ? `Uploading ${progress[slot] ?? 0}%` : `Upload ${rules[slot].label}`}</button></article> })}</div>
  </section>
}
