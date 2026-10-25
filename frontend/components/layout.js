import styles from '../styles/layout.module.css'

export default function Layout(props) {
  return (
    <div className={styles.layout}>
      <h1 className={styles.title}>
        BigCompany Knowledge Assistant
      </h1>

      <p className={styles.subtitle}>
        Powered by Google Gemini. Ask about company
        policies, engineering guidelines, or onboarding.
      </p>

      {props.children}
    </div>
  )
}