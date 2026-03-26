import React, { useEffect, useState } from 'react'

export default function Viewer({ file }) {
  const [data, setData] = useState(null)
  const [text, setText] = useState(null)
  const [isImage, setIsImage] = useState(false)

  useEffect(() => {
    if (!file) return
    const load = async () => {
      try {
        const res = await fetch('/data/' + file)
        const ct = res.headers.get('content-type') || ''
        if (ct.includes('application/json')) {
          const j = await res.json()
          setData(j)
          setText(null)
          setIsImage(false)
        } else if (ct.startsWith('image/')) {
          setIsImage(true)
          setData('/data/' + file)
          setText(null)
        } else {
          const t = await res.text()
          setText(t)
          setData(null)
          setIsImage(false)
        }
      } catch (e) {
        console.error(e)
        setData(null)
        setText('Error loading file')
      }
    }
    load()
  }, [file])

  if (!file) return <div>Select a file</div>

  return (
    <div className="viewer">
      <h3>{file}</h3>
      {isImage && <img src={data} alt={file} />}
      {text && <pre>{text}</pre>}
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  )
}
