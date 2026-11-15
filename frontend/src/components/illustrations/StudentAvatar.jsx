import React from 'react'
import StudentGirlIllustration from './StudentGirlIllustration.jsx'
import StudentBoyIllustration from './StudentBoyIllustration.jsx'
import StudentNeutralIllustration from './StudentNeutralIllustration.jsx'

const SIZE_MAP = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 48,
  xl: 64,
  '2xl': 96,
  '3xl': 120,
}

/**
 * Reusable Student Avatar with Consistent Animated Character Illustrations
 * - Girl student -> StudentGirlIllustration
 * - Boy student  -> StudentBoyIllustration
 * - Unspecified  -> StudentNeutralIllustration
 */
export default function StudentAvatar({
  student,
  gender,
  size = 'md',
  animate = true,
  className = '',
}) {
  const pixelSize = typeof size === 'number' ? size : (SIZE_MAP[size] || 40)

  // Resolve gender from prop or student object
  const rawGender = (
    gender ||
    student?.gender ||
    student?.profile?.gender ||
    student?.sex ||
    ''
  ).toString().trim().toLowerCase()

  const isFemale =
    rawGender === 'f' ||
    rawGender === 'female' ||
    rawGender === 'girl' ||
    rawGender === 'woman'

  const isMale =
    rawGender === 'm' ||
    rawGender === 'male' ||
    rawGender === 'boy' ||
    rawGender === 'man'

  if (isFemale) {
    return (
      <StudentGirlIllustration
        size={pixelSize}
        animate={animate}
        className={className}
      />
    )
  }

  if (isMale) {
    return (
      <StudentBoyIllustration
        size={pixelSize}
        animate={animate}
        className={className}
      />
    )
  }

  return (
    <StudentNeutralIllustration
      size={pixelSize}
      animate={animate}
      className={className}
    />
  )
}
