import React from 'react'

export default function FileList({ files, onSelect, selected }) {
  return (
    <ul className="file-list">
      {files.map((f) => (
        <li
          key={f}
          className={f === selected ? 'selected' : ''}
          onClick={() => onSelect(f)}
        >
          {f}
        </li>
      ))}
    </ul>
  )
}
