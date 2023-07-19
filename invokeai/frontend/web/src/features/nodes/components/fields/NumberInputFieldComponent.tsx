import {
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
} from '@chakra-ui/react';
import { useAppDispatch } from 'app/store/storeHooks';
import { numberStringRegex } from 'common/components/IAINumberInput';
import { fieldValueChanged } from 'features/nodes/store/nodesSlice';
import {
  FloatInputFieldTemplate,
  FloatInputFieldValue,
  IntegerInputFieldTemplate,
  IntegerInputFieldValue,
} from 'features/nodes/types/types';
import { memo, useEffect, useState } from 'react';
import { FieldComponentProps } from './types';

const NumberInputFieldComponent = (
  props: FieldComponentProps<
    IntegerInputFieldValue | FloatInputFieldValue,
    IntegerInputFieldTemplate | FloatInputFieldTemplate
  >
) => {
  const { nodeId, field } = props;
  const dispatch = useAppDispatch();
  const [valueAsString, setValueAsString] = useState<string>(
    String(field.value)
  );

  const handleValueChanged = (v: string) => {
    setValueAsString(v);
    // This allows negatives and decimals e.g. '-123', `.5`, `-0.2`, etc.
    if (!v.match(numberStringRegex)) {
      // Cast the value to number. Floor it if it should be an integer.
      dispatch(
        fieldValueChanged({
          nodeId,
          fieldName: field.name,
          value:
            props.template.type === 'integer'
              ? Math.floor(Number(v))
              : Number(v),
        })
      );
    }
  };

  useEffect(() => {
    if (
      !valueAsString.match(numberStringRegex) &&
      field.value !== Number(valueAsString)
    ) {
      setValueAsString(String(field.value));
    }
  }, [field.value, valueAsString]);

  return (
    <NumberInput
      onChange={handleValueChanged}
      value={valueAsString}
      step={props.template.type === 'integer' ? 1 : 0.1}
      precision={props.template.type === 'integer' ? 0 : 3}
    >
      <NumberInputField />
      <NumberInputStepper>
        <NumberIncrementStepper />
        <NumberDecrementStepper />
      </NumberInputStepper>
    </NumberInput>
  );
};

export default memo(NumberInputFieldComponent);
