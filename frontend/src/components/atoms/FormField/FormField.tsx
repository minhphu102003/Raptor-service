import { Input, Textarea } from '@heroui/react'
import { forwardRef } from 'react'

export interface BaseFormFieldProps {
  label: string
  placeholder?: string
  isRequired?: boolean
  disabled?: boolean
  isInvalid?: boolean
  errorMessage?: string
  className?: string
  autoFocus?: boolean
}

export interface InputFormFieldProps extends BaseFormFieldProps {
  type?: 'input'
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export interface TextareaFormFieldProps extends BaseFormFieldProps {
  type: 'textarea'
  minRows?: number
  maxRows?: number
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export type FormFieldProps = InputFormFieldProps | TextareaFormFieldProps

// Internal Input component
const InputField = forwardRef<HTMLInputElement, InputFormFieldProps>(
  ({ value, onChange, ...props }, ref) => {
    return (
      <Input
        label={props.label}
        placeholder={props.placeholder}
        variant="bordered"
        size="lg"
        isRequired={props.isRequired}
        disabled={props.disabled}
        isInvalid={props.isInvalid}
        errorMessage={props.errorMessage}
        className={props.className || 'w-full'}
        autoFocus={props.autoFocus}
        onChange={onChange}
        value={value}
        ref={ref}
      />
    )
  }
)

// Internal Textarea component
const TextareaField = forwardRef<HTMLInputElement, TextareaFormFieldProps>(
  ({ minRows, maxRows, value, onChange, ...props }, ref) => {
    return (
      <Textarea
        label={props.label}
        placeholder={props.placeholder}
        variant="bordered"
        size="lg"
        isRequired={props.isRequired}
        disabled={props.disabled}
        isInvalid={props.isInvalid}
        errorMessage={props.errorMessage}
        className={props.className || 'w-full'}
        autoFocus={props.autoFocus}
        minRows={minRows}
        maxRows={maxRows}
        onChange={onChange}
        value={value}
        // @ts-expect-error - HeroUI Textarea expects different ref type
        ref={ref}
      />
    )
  }
)

// Main FormField component
export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(
  ({ type = 'input', ...props }, ref) => {
    if (type === 'textarea') {
      const textareaProps = props as TextareaFormFieldProps
      return <TextareaField {...textareaProps} ref={ref} />
    }

    const inputProps = props as InputFormFieldProps
    return <InputField {...inputProps} ref={ref} />
  }
)

InputField.displayName = 'InputField'
TextareaField.displayName = 'TextareaField'
FormField.displayName = 'FormField'
