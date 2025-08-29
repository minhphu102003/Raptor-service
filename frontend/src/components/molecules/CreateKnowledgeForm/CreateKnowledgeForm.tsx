import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useState, useRef, forwardRef, useImperativeHandle } from 'react'
import { createKnowledgeSchema, type CreateKnowledgeFormData } from '../../../schemas'
import { FormField } from '../../atoms/FormField'

export interface CreateKnowledgeFormProps {
  onSubmit: (data: CreateKnowledgeFormData) => Promise<void>
  disabled?: boolean
  autoFocus?: boolean
}

export interface CreateKnowledgeFormRef {
  submit: () => void
  reset: () => void
  isValid: boolean
  isSubmitting: boolean
}

export const CreateKnowledgeForm = forwardRef<CreateKnowledgeFormRef, CreateKnowledgeFormProps>(
  ({ onSubmit, disabled = false, autoFocus = true }, ref) => {
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [hasAttemptedSubmit, setHasAttemptedSubmit] = useState(false)
    const hasAttemptedSubmitRef = useRef(false)

    const {
      register,
      handleSubmit,
      reset,
      trigger,
      formState: { errors, isValid }
    } = useForm<CreateKnowledgeFormData>({
      // @ts-expect-error - Zod version compatibility issue
      resolver: zodResolver(createKnowledgeSchema),
      mode: 'onSubmit', // Start with onSubmit mode
      reValidateMode: 'onChange', // After first validation, revalidate on change
      defaultValues: {
        name: '',
        description: ''
      }
    })

    const onSubmitForm = async (data: CreateKnowledgeFormData) => {
      setIsSubmitting(true)
      try {
        await onSubmit(data)
      } catch (error) {
        console.error('Error creating knowledge base:', error)
        throw error
      } finally {
        setIsSubmitting(false)
      }
    }

    const handleFormSubmit = () => {
      // Mark that user has attempted to submit
      hasAttemptedSubmitRef.current = true
      setHasAttemptedSubmit(true) // Force re-render
      
      // Use handleSubmit to trigger validation
      handleSubmit(
        // onValid - this runs if form is valid
        onSubmitForm,
        // onInvalid - this runs if form has errors
        (errors) => {
          console.log('Form validation errors:', errors)
          // Errors will be automatically displayed through formState.errors
        }
      )()
    }

    const resetForm = () => {
      reset()
      setIsSubmitting(false)
      setHasAttemptedSubmit(false)
      hasAttemptedSubmitRef.current = false
    }

    // Expose form methods through ref
    useImperativeHandle(ref, () => ({
      submit: handleFormSubmit,
      reset: resetForm,
      isValid,
      isSubmitting
    }))

    return (
      <div className="space-y-4">
        <div>
          <FormField
            {...register('name', {
              onChange: () => {
                // Only validate on change after first submit attempt
                if (hasAttemptedSubmit) {
                  trigger('name')
                }
              }
            })}
            label="Name"
            placeholder="Enter a name for your knowledge base"
            isRequired
            autoFocus={autoFocus}
            disabled={disabled || isSubmitting}
            isInvalid={!!errors.name}
            errorMessage={errors.name?.message}
          />
        </div>
        
        <div>
          <FormField
            {...register('description', {
              onChange: () => {
                // Only validate on change after first submit attempt
                if (hasAttemptedSubmit) {
                  trigger('description')
                }
              }
            })}
            type="textarea"
            label="Description"
            placeholder="Describe what this knowledge base contains..."
            minRows={3}
            maxRows={5}
            disabled={disabled || isSubmitting}
            isInvalid={!!errors.description}
            errorMessage={errors.description?.message}
          />
        </div>
      </div>
    )
  }
)

CreateKnowledgeForm.displayName = 'CreateKnowledgeForm'